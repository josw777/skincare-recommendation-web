import ProductCard from "../components/ProductCard";

function getSkinConditionSummary(predictions) {
    const items = Object.entries(predictions).map(([name, item]) => ({
        name,
        code: item.predicted_code,
        confidence: item.confidence,
    }));

    // confidence 높은 순으로 상위 3개만 보여줌
    return items
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 3);
}
function getSkinMessage(name) {
    const messages = {
        민감성: "자극을 줄이는 저자극 케어를 함께 고려할 수 있어요.",
        미백: "피부 톤과 관련된 케어 방향을 참고할 수 있어요.",
        주름: "보습과 탄력 케어를 함께 고려할 수 있어요.",
        여드름: "트러블·피지 조절 관련 케어를 참고할 수 있어요.",
        모공: "피지 조절과 모공 케어 방향을 함께 볼 수 있어요.",
        "피부 처짐": "탄력과 보습 중심의 케어를 참고할 수 있어요.",
        과각질: "각질 관리와 보습 균형을 함께 고려할 수 있어요.",
        붉어짐: "진정·장벽 케어 방향을 함께 고려할 수 있어요.",
    };

    return messages[name] || "추천 방향을 정하는 데 참고할 수 있어요.";
}

function ResultPage({ result, previewUrl, onReset }) {
    const imagePrediction = result.image_prediction;
    const recommendation = result.recommendation;
    const products = recommendation.related_products || [];
    const skinSummary = getSkinConditionSummary(imagePrediction.predictions);

    const reasoningSteps = Array.isArray(recommendation.reasoning_steps)
        ? recommendation.reasoning_steps
        : [
            {
                step: "1",
                title: "추천 근거",
                content: recommendation.reasoning_steps?.step1,
            },
            {
                step: "2",
                title: "추천 근거",
                content: recommendation.reasoning_steps?.step2,
            },
            {
                step: "3",
                title: "추천 근거",
                content: recommendation.reasoning_steps?.step3,
            },
        ].filter((item) => item.content);

    return (
        <section className="app-card result-page">
            <p className="section-label">추천 결과</p>
            <h2>나에게 맞는 스킨케어 제안</h2>

            <div className="notice-box">{result.notice}</div>

            <h3>추천 내용</h3>
            <div className="answer-box">{recommendation.answer}</div>

            <h3>이렇게 추천했어요</h3>
            <div className="reason-grid">
                {reasoningSteps.map((item, index) => (
                    <div key={index}>
                        <span>{item.step || index + 1}</span>
                        {item.title && <strong>{item.title}</strong>}
                        <p>{item.content}</p>
                    </div>
                ))}
            </div>

            <h3>관련 제품 후보</h3>
            <p className="small-guide">
                추천 답변에서 언급된 성분이 제품 전성분 정보에서 확인된 참고 후보입니다.
            </p>

            <div className="product-grid">
                {products.map((product, index) => (
                    <ProductCard key={index} product={product} index={index} />
                ))}
            </div>

            {/* <h3>사진 기반 피부 컨디션 참고 결과</h3>
            <p className="small-guide">
                업로드한 사진에서 추정된 피부 상태를 바탕으로 추천 방향에 참고했습니다.
            </p>

            <div className="skin-summary-card">
                <div className="skin-summary-image">
                    {previewUrl ? (
                        <img src={previewUrl} alt="분석 이미지" />
                    ) : (
                        <div className="empty-preview">이미지 없음</div>
                    )}
                </div>

                <div className="skin-summary-content">
                    <h4>주요 참고 신호</h4>

                    <div className="skin-signal-list">
                        {skinSummary.map((item) => (
                            <div className="skin-signal" key={item.name}>
                                <div>
                                    <strong>{item.name}</strong>
                                    <p>{getSkinMessage(item.name)}</p>
                                </div>
                                <span>{(item.confidence * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>

                    <p className="skin-summary-note">
                        이 결과는 의료 진단이 아니라 유사 사례 검색과 추천 방향 설정을 위한 참고 정보입니다.
                    </p>
                </div>
            </div>

            <h3>비슷한 피부 고민 사례</h3>
            <div className="case-box">
                <p><b>성별:</b> {recommendation.similar_case.gender}</p>
                <p><b>나이대:</b> {recommendation.similar_case.age_group}</p>
                <p><b>피부타입:</b> {recommendation.similar_case.skin_type}</p>
                <p><b>대표 고민:</b> {recommendation.similar_case.target_concern}</p>
                <p><b>상담 질문:</b> {recommendation.similar_case.question}</p>
            </div>

            <div className="score-strip">
                <div>
                    <span>비슷한 사례 점수</span>
                    <strong>{recommendation.final_score}</strong>
                </div>
                <div>
                    <span>고민 유사도</span>
                    <strong>{recommendation.question_score}</strong>
                </div>
                <div>
                    <span>입력 정보 일치도</span>
                    <strong>{recommendation.structured_score}</strong>
                </div>
            </div> */}

            <div className="button-row">
                <button className="primary-button" onClick={onReset}>
                    처음부터 다시 분석
                </button>
            </div>
        </section>
    );
}

export default ResultPage;  