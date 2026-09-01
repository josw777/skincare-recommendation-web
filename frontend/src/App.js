import { useEffect, useState } from "react";
import "./App.css";
import glowrLogo from "./assets/glowr-logo.png";

import StepBar from "./components/StepBar";
import UploadPage from "./pages/UploadPage";
import ConcernPage from "./pages/ConcernPage";
import LoadingPage from "./pages/LoadingPage";
import ResultPage from "./pages/ResultPage";

const mockResult = {
  notice:
    "이 결과는 의료 진단이 아니며, 피부 사진과 입력한 고민을 바탕으로 한 참고용 추천입니다.",
  image_prediction: {
    initial_skin_condition: "NS/P1/W2/NA/VP/SA/ND/R",
    predictions: {
      민감성: { predicted_code: "NS", confidence: 0.87 },
      미백: { predicted_code: "P1", confidence: 0.74 },
      주름: { predicted_code: "W2", confidence: 0.68 },
      여드름: { predicted_code: "NA", confidence: 0.81 },
      모공: { predicted_code: "VP", confidence: 0.72 },
      "피부 처짐": { predicted_code: "SA", confidence: 0.61 },
      과각질: { predicted_code: "ND", confidence: 0.79 },
      붉어짐: { predicted_code: "R", confidence: 0.83 },
    },
  },
  recommendation: {
    final_score: 0.8421,
    question_score: 0.8124,
    structured_score: 0.8718,
    answer:
      "현재 입력한 피부 고민과 비슷한 상담 사례를 기준으로 볼 때, 저자극 클렌징 후 진정 성분이 포함된 토너 또는 앰플을 사용하고, 과도한 각질 제거 제품은 피하는 방향을 추천합니다.",
    reasoning_steps: {
      step1:
        "대표 고민이 여드름과 붉어짐에 가깝고, 이미지 기반 피부상태 추정 결과에서도 관련 항목이 함께 확인되었습니다.",
      step2:
        "비슷한 상담 사례에서도 마스크 착용, 피지 증가, 붉어짐이 함께 나타나 사용자의 고민과 구조적으로 유사합니다.",
      step3:
        "따라서 자극이 강한 제품보다는 진정, 보습, 피지 조절 중심의 케어 방향이 적합한 사례로 판단됩니다.",
    },
    similar_case: {
      gender: "여성",
      age_group: "20대",
      skin_type: "지성",
      target_concern: "여드름",
      skin_condition: "NS/P1/W2/NA/VP/SA/ND/R",
      question:
        "마스크 착용 이후 여드름과 붉어짐이 심해졌는데 어떤 스킨케어가 좋을까요?",
    },
    related_products: [
      {
        product_name: "시카 진정 토너",
        brand: "Sample Brand",
        category: "토너",
        matched_keywords: ["진정", "병풀", "붉어짐"],
        main_ingredients: "병풀추출물, 판테놀, 알란토인",
        reason:
          "대표 고민인 붉어짐과 민감성 관련 키워드가 제품 정보와 매칭되었습니다.",
      },
      {
        product_name: "저자극 수분 앰플",
        brand: "Sample Brand",
        category: "앰플",
        matched_keywords: ["보습", "저자극", "장벽"],
        main_ingredients: "히알루론산, 세라마이드, 판테놀",
        reason:
          "유사 사례의 추천 방향인 보습·장벽 케어와 관련된 제품 후보입니다.",
      },
      {
        product_name: "트러블 케어 젤",
        brand: "Sample Brand",
        category: "스팟 케어",
        matched_keywords: ["트러블", "피지", "진정"],
        main_ingredients: "티트리추출물, 살리실산, 병풀추출물",
        reason:
          "대표 고민과 관련된 트러블·피지 조절 키워드가 포함되어 있습니다.",
      },
    ],
  },
};

function App() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");

  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    gender: "",
    age: "",
    skinType: "",
    skinConcerns: [],   // 여러 개 선택
    targetConcern: "",  // 그중 대표 고민 1개

    question: "",
  });

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [step, loading]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (!file) return;

    setImageFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleCapturedImage = (file) => {
    if (!file) return;

    setImageFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const setFormValue = (name, value) => {
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleTextChange = (e) => {
    const { name, value } = e.target;
    setFormValue(name, value);
  };

  const goToConcernPage = () => {
    if (!imageFile) {
      alert("피부 사진을 먼저 올려주세요.");
      return;
    }

    setStep(2);
  };

  const startAnalysis = async () => {
    if (
      !form.gender ||
      !form.age ||
      !form.skinType ||
      form.skinConcerns.length === 0 ||
      !form.targetConcern ||
      !form.question
    ) {
      alert("필수 정보를 모두 입력해주세요.");
      return;
    }

    setStep(3);
    setLoading(true);
    setResult(null);

    try {
      console.log("분석 요청 시작");
      console.log("form:", form);
      console.log("imageFile:", imageFile);

      const formData = new FormData();

      const skinConcernsText = Array.isArray(form.skinConcerns)
        ? form.skinConcerns.join(", ")
        : form.skinConcerns;

      formData.append("image", imageFile);
      formData.append("gender", form.gender);
      formData.append("age", form.age);
      formData.append("skin_type", form.skinType);
      formData.append("skin_concerns", skinConcernsText);
      formData.append("target_concern", form.targetConcern);

      formData.append("question", form.question);

      console.log("fetch 직전");

      const response = await fetch("/api/predict-recommend", {
        method: "POST",
        body: formData,
      });

      console.log("fetch 응답:", response);

      if (!response.ok) {
        throw new Error("서버 요청 실패");
      }

      const data = await response.json();
      console.log("서버 응답 데이터:", data);

      setResult(data);
    } catch (error) {
      console.error("분석 요청 에러:", error);
      alert("분석 중 오류가 발생했습니다. 콘솔 로그를 확인해주세요.");
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(1);
    setLoading(false);
    setImageFile(null);
    setPreviewUrl("");
    setResult(null);
    setForm({
      gender: "",
      age: "",
      skinType: "",
      skinConcerns: [],
      targetConcern: "",

      question: "",
    });
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand-area">
          <img src={glowrLogo} alt="GLOWR 로고" className="brand-logo" />

          <div>
            <h1>내 피부에 맞는 스킨케어 찾기</h1>
            <p>
              사진과 피부 고민을 바탕으로 비슷한 상담 사례와 관련 제품 후보를 찾아드려요.
            </p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <StepBar step={step} />

        {step === 1 && (
          <UploadPage
            previewUrl={previewUrl}
            onImageChange={handleImageChange}
            onCaptureImage={handleCapturedImage}
            onNext={() => setStep(2)}
          />
        )}

        {step === 2 && (
          <ConcernPage
            form={form}
            previewUrl={previewUrl}
            setFormValue={setFormValue}
            onChange={handleTextChange}
            onPrev={() => setStep(1)}
            onSubmit={startAnalysis}
          />
        )}

        {step === 3 && loading && <LoadingPage />}

        {step === 3 && !loading && result && (
          <ResultPage result={result} previewUrl={previewUrl} onReset={reset} />
        )}
      </main>
    </div>
  );
}

export default App;