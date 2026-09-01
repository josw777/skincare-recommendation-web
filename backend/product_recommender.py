import re
import math
from collections import Counter

import pymysql


class ProductRecommender:
    def __init__(
        self,
        host="localhost",
        user="root",
        password="123456",
        database="cosmetic",
        port=3306,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port

        print("제품 DB 로딩 중...")
        self.products = self._load_products()

        for product in self.products:
            ingredients = self._safe_text(product.get("ingredients"))
            ingredient_list = self._split_ingredients(ingredients)

            product["ingredient_list"] = ingredient_list
            product["ingredient_text"] = " ".join(ingredient_list)
            product["ingredient_norm_text"] = self._normalize(product["ingredient_text"])

        self.ingredient_vocab = self._build_ingredient_vocab()

        print("제품 수:", len(self.products))
        print("성분 후보 수:", len(self.ingredient_vocab))
        print("제품 DB 로딩 완료")

    def _connect(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def _normalize(self, text):
        text = self._safe_text(text).lower()
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[()\[\]{}·ㆍ,./\-_:;\"'‘’“”]", "", text)
        return text

    def _remove_contained_keywords(self, items):
        """
        쑥잎추출물, 쑥잎처럼 긴 성분명 안에 포함되는 짧은 단어는 제거
        """
        result = []

        for item in items:
            norm_item = self._normalize(item)

            is_contained = False

            for other in items:
                if item == other:
                    continue

                norm_other = self._normalize(other)

                if len(norm_item) < len(norm_other) and norm_item in norm_other:
                    is_contained = True
                    break

            if not is_contained and item not in result:
                result.append(item)

        return result

    def _load_products(self):
        sql = """
            SELECT
                id,
                product_name,
                brand,
                category,
                capacity,
                specification,
                ingredients,
                rating,
                review_count,
                goods_id
            FROM cosmetic_products
            WHERE product_name IS NOT NULL
        """

        conn = self._connect()

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
        finally:
            conn.close()

        return rows

    def _safe_text(self, value):
        if value is None:
            return ""
        return str(value)

    def _to_float(self, value, default=0.0):
        try:
            value = str(value).replace(",", "").strip()
            if not value:
                return default
            return float(value)
        except:
            return default

    def _to_int(self, value, default=0):
        try:
            value = str(value).replace(",", "").strip()
            if not value:
                return default
            return int(float(value))
        except:
            return default

    def _clean_ingredient(self, text):
        text = self._safe_text(text)

        text = re.sub(r"\([^)]*\)", "", text)
        text = re.sub(r"\[[^\]]*\]", "", text)
        text = re.sub(r"\d+(\.\d+)?\s*(ppm|PPM|%|ppb|PPB)", "", text)
        text = text.strip()

        return text

    def _split_ingredients(self, ingredients):
        ingredients = self._safe_text(ingredients)

        if not ingredients:
            return []

        if "상품상세참조" in ingredients or "상세참조" in ingredients:
            return []

        raw_items = re.split(r"[,;，\n]", ingredients)

        result = []

        for item in raw_items:
            item = self._clean_ingredient(item)

            if len(item) < 2:
                continue

            if item not in result:
                result.append(item)

        return result

    def _build_ingredient_vocab(self):
        """
        제품 DB에 실제 등장하는 성분명만 후보로 사용.
        너무 많은 제품에 공통으로 들어간 성분은 자동 제외.
        예: 정제수, 글리세린, 1,2-헥산다이올 같은 범용 성분
        """
        doc_counter = Counter()

        for product in self.products:
            for ingredient in set(product["ingredient_list"]):
                doc_counter[ingredient] += 1

        total_products = len(self.products)
        vocab = []

        for ingredient, count in doc_counter.items():
            doc_ratio = count / total_products

            # 너무 흔한 성분은 추천 근거로 약하므로 제외
            if doc_ratio > 0.45:
                continue

            if len(ingredient) < 2:
                continue

            vocab.append(ingredient)

        # 긴 성분명을 먼저 찾기 위해 길이순 정렬
        vocab = sorted(vocab, key=len, reverse=True)

        return vocab

    def _reasoning_to_text(self, reasoning_steps):
        if reasoning_steps is None:
            return ""

        if isinstance(reasoning_steps, dict):
            return " ".join(map(str, reasoning_steps.values()))

        if isinstance(reasoning_steps, list):
            texts = []

            for step in reasoning_steps:
                if isinstance(step, dict):
                    texts.append(str(step.get("title", "")))
                    texts.append(str(step.get("content", "")))
                else:
                    texts.append(str(step))

            return " ".join(texts)

        return str(reasoning_steps)

    def _extract_ingredients_from_answer(self, answer_text, reasoning_steps=None):
        """
        추천 답변/추천 근거 안에서 DB에 실제 존재하는 성분명을 추출.
        사람이 고민별 키워드를 직접 만들지 않음.
        """
        reasoning_text = self._reasoning_to_text(reasoning_steps)

        source_text = f"{answer_text} {reasoning_text}"
        source_norm_text = self._normalize(source_text)

        extracted = []

        bad_words = {
            "정제수", "글리세린", "부틸렌글라이콜", "다이프로필렌글라이콜",
            "1,2-헥산다이올", "카프릴릴글라이콜", "에틸헥실글리세린",
            "페녹시에탄올", "향료", "성분", "추출물", "오일", "줄기", "잎",
            "피부", "관리", "추천", "사용", "효과", "도움"
        }

        # 1. DB 성분명이 답변 안에 직접 등장하는 경우
        for ingredient in self.ingredient_vocab:
            norm_ingredient = self._normalize(ingredient)

            if not norm_ingredient:
                continue

            if ingredient in bad_words or norm_ingredient in bad_words:
                continue

            if len(norm_ingredient) < 3:
                continue

            if norm_ingredient in source_norm_text:
                extracted.append(ingredient)

        # 2. 너무 긴 성분명이 잡혔을 때, 대표 검색어도 추가
        # 예: 쑥잎추출물 -> 쑥잎
        extra = []

        for ingredient in extracted:
            if ingredient.endswith("추출물"):
                base = ingredient.replace("추출물", "").strip()

                if len(base) >= 2 and base not in bad_words:
                    extra.append(base)

        extracted.extend(extra)

        # 중복 제거
        result = []

        for item in extracted:
            if item not in result:
                result.append(item)

        return result

    def recommend_products(
        self,
        target_concern,
        skin_concerns="",
        skin_type="",
        answer_text="",
        reasoning_steps=None,
        limit=3,
    ):
        extracted_ingredients = self._extract_ingredients_from_answer(
            answer_text=answer_text,
            reasoning_steps=reasoning_steps,
        )

        print("===== 답변에서 추출된 성분 =====")
        print(extracted_ingredients)
        print("=============================")

        # 추천 답변에 성분명이 없으면 억지로 제품을 추천하지 않음
        if not extracted_ingredients:
            return []

        products = []

        for row in self.products:
            ingredient_norm_text = row.get("ingredient_norm_text", "")

            matched_ingredients = []

            for ingredient in extracted_ingredients:
                norm_ingredient = self._normalize(ingredient)

                if norm_ingredient and norm_ingredient in ingredient_norm_text:
                    matched_ingredients.append(ingredient)

            matched_ingredients = self._remove_contained_keywords(matched_ingredients)

            match_count = len(matched_ingredients)

            if match_count == 0:
                continue

            rating = self._to_float(row.get("rating"), 0.0)
            review_count = self._to_int(row.get("review_count"), 0)

            product_score = (
                match_count * 10
                + rating
                + math.log1p(review_count) * 0.5
            )

            ingredients = self._safe_text(row.get("ingredients"))

            if "상품상세참조" in ingredients or "상세참조" in ingredients:
                ingredient_preview = ["전성분 정보 없음"]
            else:
                ingredient_preview = [
                    item.strip()
                    for item in ingredients.replace(";", ",").split(",")
                    if item.strip()
                ][:5]

            products.append({
                "id": row.get("id"),
                "product_name": self._safe_text(row.get("product_name")),
                "brand": self._safe_text(row.get("brand")),
                "category": self._safe_text(row.get("category")),
                "capacity": self._safe_text(row.get("capacity")),
                "rating": round(rating, 2),
                "review_count": review_count,
                "goods_id": self._safe_text(row.get("goods_id")),

                "main_ingredients": ingredient_preview,

                "matched_ingredients": matched_ingredients[:6],
                "matched_keywords": matched_ingredients[:6],
                "match_count": match_count,
                "product_score": round(product_score, 4),

                "reason": (
                    f"추천 답변에서 언급된 성분 "
                    f"'{', '.join(matched_ingredients[:3])}'이 제품 전성분에서 확인되어 "
                    f"관련 제품 후보로 선정되었습니다."
                )
            })

        print("===== 제품 성분 매칭 결과 =====")
        for p in products[:10]:
            print("상품명:", p["product_name"])
            print("브랜드:", p["brand"])
            print("연결 성분:", p["matched_ingredients"])
            print("match_count:", p["match_count"])
            print("product_score:", p["product_score"])
            print("--------------------------------")
        print("=============================")

        products = sorted(
            products,
            key=lambda x: (
                x["match_count"],
                x["product_score"],
                x["rating"],
                x["review_count"]
            ),
            reverse=True
        )

        return products[:limit]