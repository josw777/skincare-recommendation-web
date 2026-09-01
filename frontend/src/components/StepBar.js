function StepBar({ step }) {
    return (
        <div className="step-bar">
            <div className={step >= 1 ? "active" : ""}>1. 사진 등록</div>
            <div className={step >= 2 ? "active" : ""}>2. 고민 입력</div>
            <div className={step >= 3 ? "active" : ""}>3. 추천 확인</div>
        </div>
    );
}

export default StepBar;