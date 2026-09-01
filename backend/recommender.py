import ast
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "artifacts"

DF_PATH = ARTIFACT_DIR / "train_json_df.pkl"
EMBEDDING_PATH = ARTIFACT_DIR / "train_question_embeddings.npy"

SBERT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SkincareRecommender:
    def __init__(self):
        print("추천 모델 로딩 중...")

        self.df = pd.read_pickle(DF_PATH).reset_index(drop=True)
        self.question_embeddings = np.load(EMBEDDING_PATH)

        if len(self.df) != len(self.question_embeddings):
            raise ValueError(
                f"추천 데이터 개수와 임베딩 개수가 다릅니다. "
                f"df={len(self.df)}, embeddings={len(self.question_embeddings)}"
            )

        self.model = SentenceTransformer(SBERT_MODEL_NAME)

        print("추천 데이터 컬럼:", list(self.df.columns))
        print("추천 데이터 개수:", len(self.df))
        print("임베딩 shape:", self.question_embeddings.shape)
        print("추천 모델 로딩 완료")

    def _get_col(self, candidates):
        for col in candidates:
            if col in self.df.columns:
                return col
        return None

    def _safe_value(self, row, col):
        if col is None:
            return ""

        value = row.get(col, "")

        if value is None:
            return ""

        if isinstance(value, float) and pd.isna(value):
            return ""

        return value

    def _safe_to_list(self, x):
        if isinstance(x, list):
            return x

        if isinstance(x, tuple):
            return list(x)

        if x is None:
            return []

        if isinstance(x, float) and pd.isna(x):
            return []

        if isinstance(x, str):
            x = x.strip()

            if not x:
                return []

            try:
                parsed = ast.literal_eval(x)
                if isinstance(parsed, list):
                    return parsed
            except:
                pass

            # 사용자가 "모공, 미백" 또는 "모공/미백"처럼 보낸 경우
            if "," in x or "/" in x:
                parts = (
                    x.replace("/", ",")
                    .replace("|", ",")
                    .split(",")
                )
                return [p.strip() for p in parts if p.strip()]

            return [x]

        return [str(x)]

    def _list_to_text(self, x):
        items = self._safe_to_list(x)
        return " ".join(map(str, items))

    def _external_factor_list(self, external):
        external = self._safe_to_list(external)

        factors = []

        for item in external:
            if isinstance(item, dict):
                factor = item.get("factor")
                if factor:
                    factors.append(str(factor))
            else:
                factors.append(str(item))

        return factors

    def _age_to_group(self, age):
        try:
            age = int(age)
        except:
            return ""

        if age < 20:
            return "10대"
        elif age < 30:
            return "20대"
        elif age < 40:
            return "30대"
        elif age < 50:
            return "40대"
        elif age < 60:
            return "50대"
        else:
            return "60대 이상"

    def _exact_match_score(self, a, b):
        a = str(a).strip()
        b = str(b).strip()

        if not a or not b:
            return 0.0

        return 1.0 if a == b else 0.0

    def _jaccard_similarity(self, a, b):
        a_list = self._safe_to_list(a)
        b_list = self._safe_to_list(b)

        set_a = set(map(str, a_list))
        set_b = set(map(str, b_list))

        if len(set_a | set_b) == 0:
            return 0.0

        return len(set_a & set_b) / len(set_a | set_b)

    def _external_jaccard(self, a, b):
        a_factors = self._external_factor_list(a)
        b_factors = self._external_factor_list(b)

        return self._jaccard_similarity(a_factors, b_factors)

    def _condition_match_score(self, cond1, cond2):
        if not isinstance(cond1, str) or not isinstance(cond2, str):
            return 0.0

        codes1 = cond1.split("/")
        codes2 = cond2.split("/")

        if len(codes1) != len(codes2):
            return 0.0

        return sum(a == b for a, b in zip(codes1, codes2)) / len(codes1)

    def _age_group_match_score(self, age1, age2):
        return 1.0 if self._age_to_group(age1) == self._age_to_group(age2) else 0.0

    def _format_cot_steps(self, cot):
        """
        chain_of_thought를 Flask JSON 응답에 안전하게 넣기 위한 함수
        """
        if isinstance(cot, list):
            formatted = []

            for item in cot:
                if isinstance(item, dict):
                    formatted.append({
                        "step": str(item.get("step", "")),
                        "title": str(item.get("title", "")),
                        "content": str(item.get("content", ""))
                    })
                else:
                    formatted.append({
                        "step": "",
                        "title": "",
                        "content": str(item)
                    })

            return formatted

        if isinstance(cot, str):
            try:
                parsed = ast.literal_eval(cot)
                if isinstance(parsed, list):
                    return self._format_cot_steps(parsed)
            except:
                pass

            return [{
                "step": "",
                "title": "추천 근거",
                "content": cot
            }]

        return [{
            "step": "",
            "title": "추천 근거",
            "content": "사용자 질문과 입력 조건이 유사한 상담 사례를 기준으로 추천 방향을 산출했습니다."
        }]

    def recommend(
        self,
        gender,
        age,
        skin_type,
        skin_concerns,
        target_concern,

        question,
        initial_skin_condition,
        top_k=5,
    ):
        question_col = self._get_col([
            "question", "Question", "질문", "input", "user_question"
        ])

        answer_col = self._get_col([
            "answer", "Answer", "답변", "response", "추천답변"
        ])

        cot_col = self._get_col([
            "chain_of_thought", "cot", "CoT", "reasoning", "추론근거"
        ])

        gender_col = self._get_col([
            "gender", "성별"
        ])

        age_col = self._get_col([
            "age", "age_group", "나이", "나이대", "연령대"
        ])

        skin_type_col = self._get_col([
            "skin_type", "피부타입"
        ])

        concern_col = self._get_col([
            "skin_concerns", "concern", "피부고민", "전체피부고민"
        ])

        target_col = self._get_col([
            "target_concern", "대표고민", "main_concern"
        ])

        condition_col = self._get_col([
            "initial_skin_condition", "skin_condition", "피부상태코드"
        ])


        if question_col is None:
            raise ValueError("질문 컬럼을 찾지 못했습니다. train_json_df.pkl의 컬럼명을 확인해야 합니다.")

        if answer_col is None:
            raise ValueError("답변 컬럼을 찾지 못했습니다. train_json_df.pkl의 컬럼명을 확인해야 합니다.")

        if condition_col is None:
            raise ValueError("피부상태 코드 컬럼을 찾지 못했습니다. initial_skin_condition 컬럼을 확인해야 합니다.")

        # 1. 대표 고민 필터링
        candidates = self.df.copy()
        candidate_idx = candidates.index.to_numpy()

        if target_col is not None and target_concern:
            exact_filtered = candidates[
                candidates[target_col].astype(str) == str(target_concern)
            ]

            if len(exact_filtered) > 0:
                candidates = exact_filtered.copy()
                candidate_idx = candidates.index.to_numpy()
            else:
                contains_filtered = candidates[
                    candidates[target_col].astype(str).str.contains(str(target_concern), na=False, regex=False)
                ]

                if len(contains_filtered) > 0:
                    candidates = contains_filtered.copy()
                    candidate_idx = candidates.index.to_numpy()

        # 2. 질문 의미 유사도
        user_embedding = self.model.encode(
            [str(question)],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        candidate_embeddings = self.question_embeddings[candidate_idx]

        question_scores = cosine_similarity(
            user_embedding,
            candidate_embeddings
        ).flatten()

        candidates["question_score"] = question_scores

        # 3. 구조화 정보 점수
        skin_concern_scores = []
        condition_scores = []

        skin_type_scores = []
        age_scores = []
        gender_scores = []
        structured_scores = []

        for _, row in candidates.iterrows():
            case_gender = self._safe_value(row, gender_col)
            case_age = self._safe_value(row, age_col)
            case_skin_type = self._safe_value(row, skin_type_col)
            case_concerns = self._safe_value(row, concern_col)
            case_condition = self._safe_value(row, condition_col)


            skin_concern_score = self._jaccard_similarity(
                skin_concerns,
                case_concerns
            )

            condition_score = self._condition_match_score(
                str(initial_skin_condition),
                str(case_condition)
            )



            skin_type_score = self._exact_match_score(
                skin_type,
                case_skin_type
            )

            age_score = self._age_group_match_score(
                age,
                case_age
            )

            gender_score = self._exact_match_score(
                gender,
                case_gender
            )

            structured_score = (
                skin_concern_score +
                condition_score +
                skin_type_score +
                age_score +
                gender_score
            ) / 5

            skin_concern_scores.append(skin_concern_score)
            condition_scores.append(condition_score)

            skin_type_scores.append(skin_type_score)
            age_scores.append(age_score)
            gender_scores.append(gender_score)
            structured_scores.append(structured_score)

        candidates["skin_concern_score"] = skin_concern_scores
        candidates["condition_score"] = condition_scores

        candidates["skin_type_score"] = skin_type_scores
        candidates["age_score"] = age_scores
        candidates["gender_score"] = gender_scores
        candidates["structured_score"] = structured_scores

        # 4. 최종 Hybrid Score
        candidates["final_score"] = (
            candidates["question_score"] +
            candidates["structured_score"]
        ) / 2

        top_cases = candidates.sort_values(
            "final_score",
            ascending=False
        ).head(top_k)

        best = top_cases.iloc[0]

        answer = self._safe_value(best, answer_col)
        cot = self._safe_value(best, cot_col)
        cot_steps = self._format_cot_steps(cot)

        result = {
            "final_score": round(float(best["final_score"]), 4),
            "question_score": round(float(best["question_score"]), 4),
            "structured_score": round(float(best["structured_score"]), 4),

            "score_detail": {
                "skin_concern_score": round(float(best["skin_concern_score"]), 4),
                "condition_score": round(float(best["condition_score"]), 4),

                "skin_type_score": round(float(best["skin_type_score"]), 4),
                "age_score": round(float(best["age_score"]), 4),
                "gender_score": round(float(best["gender_score"]), 4),
            },

            "answer": str(answer),

            "reasoning_steps": cot_steps,

            "similar_case": {
                "source_survey_id": str(self._safe_value(best, self._get_col(["source_survey_id", "id"]))),
                "gender": str(self._safe_value(best, gender_col)),
                "age": str(self._safe_value(best, age_col)),
                "skin_type": str(self._safe_value(best, skin_type_col)),
                "skin_concerns": str(self._safe_value(best, concern_col)),
                "target_concern": str(self._safe_value(best, target_col)),
                "skin_condition": str(self._safe_value(best, condition_col)),
                "question": str(self._safe_value(best, question_col)),
            },

            "top_cases": [
                {
                    "source_survey_id": str(self._safe_value(row, self._get_col(["source_survey_id", "id"]))),
                    "target_concern": str(self._safe_value(row, target_col)),
                    "question_score": round(float(row["question_score"]), 4),
                    "structured_score": round(float(row["structured_score"]), 4),
                    "final_score": round(float(row["final_score"]), 4),
                    "skin_condition": str(self._safe_value(row, condition_col)),
                    "question": str(self._safe_value(row, question_col)),
                }
                for _, row in top_cases.iterrows()
            ],

            "related_products": []
        }

        return result