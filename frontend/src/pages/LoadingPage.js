function LoadingPage() {
    return (
        <section className="loading-page">
            <div className="loading-card">
                <div className="loading-symbol">✨</div>

                <h2>피부 고민을 분석하고 있어요</h2>
                <p>사진과 입력한 고민을 바탕으로 비슷한 사례를 찾는 중입니다.</p>

                <div className="loading-steps">
                    <div className="done">얼굴 이미지 특징 확인 중</div>
                    <div className="done">피부 상태 코드 추정 중</div>
                    <div className="active">유사 상담 사례 검색 중</div>
                    <div>관련 제품 후보 조회 중</div>
                </div>
            </div>
        </section>
    );
}

export default LoadingPage;