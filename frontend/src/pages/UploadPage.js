import { useEffect, useRef, useState } from "react";

function UploadPage({ previewUrl, onImageChange, onCaptureImage, onNext }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);

    const [cameraOpen, setCameraOpen] = useState(false);
    const [cameraError, setCameraError] = useState("");

    useEffect(() => {
        if (cameraOpen && videoRef.current && streamRef.current) {
            videoRef.current.srcObject = streamRef.current;

            videoRef.current.play().catch((error) => {
                console.error("video play error:", error);
            });
        }
    }, [cameraOpen]);

    const startCamera = async () => {
        setCameraError("");

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setCameraError("현재 브라우저에서 카메라 기능을 지원하지 않습니다.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false,
            });

            streamRef.current = stream;
            setCameraOpen(true);

            // video 태그가 렌더링될 시간을 조금 기다린 뒤 연결
            setTimeout(async () => {
                if (!videoRef.current) {
                    setCameraError("카메라 화면을 표시할 video 태그를 찾지 못했습니다.");
                    return;
                }

                videoRef.current.srcObject = stream;

                try {
                    await videoRef.current.play();
                    console.log("카메라 재생 성공");
                } catch (playError) {
                    console.error("video play error:", playError);
                    setCameraError("카메라 화면 재생에 실패했습니다.");
                }
            }, 300);
        } catch (error) {
            console.error("카메라 실행 오류:", error);

            if (error.name === "NotAllowedError") {
                setCameraError("카메라 권한이 거부되었습니다. 브라우저 권한을 허용해주세요.");
            } else if (error.name === "NotFoundError") {
                setCameraError("사용 가능한 카메라를 찾을 수 없습니다.");
            } else if (error.name === "NotReadableError") {
                setCameraError("다른 프로그램에서 카메라를 사용 중일 수 있습니다.");
            } else {
                setCameraError("카메라를 실행할 수 없습니다.");
            }
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }

        setCameraOpen(false);
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;

        if (video.videoWidth === 0 || video.videoHeight === 0) {
            setCameraError("카메라 화면이 준비된 뒤 다시 촬영해주세요.");
            return;
        }

        const canvas = canvasRef.current;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(
            (blob) => {
                if (!blob) return;

                const file = new File([blob], "webcam-capture.jpg", {
                    type: "image/jpeg",
                });

                onCaptureImage(file);
                stopCamera();
            },
            "image/jpeg",
            0.95
        );
    };

    return (
        <section className="app-card upload-page compact-upload">
            <div className="page-title-row">
                <p className="section-label">사진 등록</p>
                <h2>피부 사진을 올려주세요</h2>
                <p className="description">
                    정면 얼굴이 잘 보이는 사진을 선택하면 더 비슷한 케어 사례를 찾을 수 있어요.
                </p>
            </div>

            <label className={previewUrl ? "upload-box has-image" : "upload-box"}>
                <input
                    type="file"
                    accept="image/*"
                    capture="user"
                    onChange={onImageChange}
                />

                {previewUrl ? (
                    <>
                        <img src={previewUrl} alt="업로드 이미지" className="upload-preview-img" />
                        <div className="upload-overlay">
                            <strong>사진 다시 선택하기</strong>
                            <span>다른 사진으로 변경할 수 있어요</span>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="upload-icon">📷</div>
                        <strong>사진 선택 또는 촬영</strong>
                        <span>jpg, png 파일을 사용할 수 있어요</span>
                    </>
                )}
            </label>

            <div className="camera-actions">
                {!cameraOpen ? (
                    <button type="button" className="secondary-button" onClick={startCamera}>
                        웹캠으로 촬영하기
                    </button>
                ) : (
                    <>
                        <button type="button" className="primary-button" onClick={capturePhoto}>
                            현재 화면 촬영
                        </button>

                        <button type="button" className="secondary-button" onClick={stopCamera}>
                            카메라 끄기
                        </button>
                    </>
                )}
            </div>

            {cameraError && <p className="error-message">{cameraError}</p>}

            {cameraOpen && (
                <div className="camera-box">
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="camera-video"
                    />
                    <canvas ref={canvasRef} style={{ display: "none" }} />
                </div>
            )}

            <div className="tip-card">
                <h3>촬영 TIP</h3>
                <ul>
                    <li>밝은 조명에서 촬영해주세요.</li>
                    <li>정면 얼굴이 잘 보이게 촬영해주세요.</li>
                    <li>과한 필터가 적용된 사진은 피해주세요.</li>
                </ul>
            </div>

            <div className="form-actions">
                <button
                    className="primary-button"
                    onClick={onNext}
                    disabled={!previewUrl}
                >
                    다음
                </button>
            </div>
        </section>
    );
}

export default UploadPage;