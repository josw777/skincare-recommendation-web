import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from io import BytesIO
from PIL import Image
from recommender import SkincareRecommender
from product_recommender import ProductRecommender

from image_model import SkinImagePredictor

app = Flask(__name__)
image_predictor = SkinImagePredictor()
recommender = SkincareRecommender()
CORS(app)

product_recommender = ProductRecommender(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "cosmetic"),
    port=int(os.getenv("DB_PORT", "3306")),
)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask server is running"})


@app.route("/api/predict-recommend", methods=["POST"])
def predict_recommend():
    image = request.files.get("image")

    gender = request.form.get("gender", "")
    age = request.form.get("age", "")
    skin_type = request.form.get("skin_type", "")
    skin_concerns = request.form.get("skin_concerns", "")
    target_concern = request.form.get("target_concern", "")

    question = request.form.get("question", "")

    if image is None:
        return jsonify({"error": "이미지 파일이 없습니다."}), 400

    pil_image = Image.open(BytesIO(image.read())).convert("RGB")

    image_result = image_predictor.predict(pil_image)

    print("===== 실제 이미지 모델 예측 결과 =====")
    print(image_result)
    print("===================================")

    recommendation_result = recommender.recommend(
        gender=gender,
        age=age,
        skin_type=skin_type,
        skin_concerns=skin_concerns,
        target_concern=target_concern,
        question=question,
        initial_skin_condition=image_result["initial_skin_condition"],
    )

    related_products = product_recommender.recommend_products(
        target_concern=target_concern,
        skin_concerns=skin_concerns,
        skin_type=skin_type,
        answer_text=recommendation_result.get("answer", ""),
        reasoning_steps=recommendation_result.get("reasoning_steps", []),
        limit=3,
    )

    recommendation_result["related_products"] = related_products

    # print("===== 제품 추천 결과 확인 =====")
    #
    # for p in related_products:
    #     print("상품명:", p["product_name"])
    #     print("브랜드:", p["brand"])
    #     print("semantic_score:", p.get("semantic_score"))
    #     print("keyword_score:", p.get("keyword_score"))
    #     print("matched_keywords:", p.get("matched_keywords"))
    #     print("product_score:", p.get("product_score"))
    #     print("주요 성분:", p.get("main_ingredients"))
    #     print("추천 이유:", p.get("reason"))
    #     print("--------------------------------")

    print("===== 실제 추천 결과 =====")
    print(recommendation_result)
    print("=========================")

    result = {
        "notice": "이 결과는 의료 진단이 아니며, 피부 사진과 입력한 고민을 바탕으로 한 참고용 추천입니다.",
        "image_prediction": image_result,
        "recommendation": recommendation_result,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)