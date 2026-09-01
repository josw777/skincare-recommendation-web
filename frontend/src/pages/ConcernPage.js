import ChipButton from "../components/ChipButton";

const concernOptions = [
    "여드름",
    "붉어짐",
    "모공",
    "민감성",
    "미백",
    "주름",
    "과각질",
    "피부 처짐",
];

const skinTypeOptions = ["건성", "지성", "복합성", "중성", "민감성"];

function ConcernPage({
    form,
    previewUrl,
    setFormValue,
    onChange,
    onPrev,
    onSubmit,
}) {
    const toggleConcern = (item) => {
        const alreadySelected = form.skinConcerns.includes(item);

        let nextConcerns;

        if (alreadySelected) {
            nextConcerns = form.skinConcerns.filter((concern) => concern !== item);
        } else {
            nextConcerns = [...form.skinConcerns, item];
        }

        setFormValue("skinConcerns", nextConcerns);

        // 대표 고민이 전체 고민에서 해제되면 대표 고민도 초기화
        if (form.targetConcern === item && alreadySelected) {
            setFormValue("targetConcern", "");
        }
    };

    return (
        <section className="app-card">
            <p className="section-label">고민 입력</p>
            <h2>피부 고민을 알려주세요</h2>
            <p className="description">
                해당되는 피부 고민을 여러 개 선택하고, 그중 가장 신경 쓰이는 대표 고민을 골라주세요.
            </p>

            <div className="ready-card">
                <div className="ready-image">
                    {previewUrl ? <img src={previewUrl} alt="준비된 사진" /> : "사진"}
                </div>
                <div>
                    <strong>사진이 준비되었습니다</strong>
                    <p>이제 피부 고민 정보를 입력해주세요.</p>
                </div>
            </div>

            <div className="input-section">
                <h3>전체 피부 고민</h3>
                <p className="small-guide">해당되는 고민을 여러 개 선택할 수 있어요.</p>

                <div className="chip-grid">
                    {concernOptions.map((item) => (
                        <ChipButton
                            key={item}
                            label={item}
                            selected={form.skinConcerns.includes(item)}
                            onClick={() => toggleConcern(item)}
                        />
                    ))}
                </div>
            </div>

            <div className="input-section">
                <h3>대표 고민</h3>
                <p className="small-guide">
                    선택한 고민 중 가장 신경 쓰이는 고민을 하나 골라주세요.
                </p>

                {form.skinConcerns.length > 0 ? (
                    <div className="chip-grid">
                        {form.skinConcerns.map((item) => (
                            <ChipButton
                                key={item}
                                label={item}
                                selected={form.targetConcern === item}
                                onClick={() => setFormValue("targetConcern", item)}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="empty-select-guide">
                        먼저 전체 피부 고민을 선택해주세요.
                    </div>
                )}
            </div>

            <div className="input-section">
                <h3>피부 타입</h3>
                <div className="chip-grid">
                    {skinTypeOptions.map((item) => (
                        <ChipButton
                            key={item}
                            label={item}
                            selected={form.skinType === item}
                            onClick={() => setFormValue("skinType", item)}
                        />
                    ))}
                </div>
            </div>

            <div className="form-grid">
                <label>
                    성별
                    <select name="gender" value={form.gender} onChange={onChange}>
                        <option value="">선택</option>
                        <option value="여성">여성</option>
                        <option value="남성">남성</option>
                    </select>
                </label>

                <label>
                    나이
                    <input
                        type="number"
                        name="age"
                        value={form.age}
                        onChange={onChange}
                        placeholder="예: 25"
                    />
                </label>
            </div>



            <label>
                질문
                <textarea
                    name="question"
                    value={form.question}
                    onChange={onChange}
                    placeholder="예: 여드름과 붉어짐이 있을 때 어떤 스킨케어를 하면 좋을까요?"
                />
            </label>

            <div className="button-row">
                <button className="secondary-button" onClick={onPrev}>
                    이전
                </button>
                <button className="primary-button" onClick={onSubmit}>
                    분석 시작하기
                </button>
            </div>
        </section>
    );
}

export default ConcernPage; 