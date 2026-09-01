// function ProductCard({ product, index }) {
//     return (
//         <div className="product-card">
//             <div className="product-head">
//                 <span className="product-rank">{index + 1}</span>
//                 <div>
//                     <h4>{product.product_name}</h4>
//                     <p>{product.brand} · {product.category}</p>
//                 </div>
//             </div>

//             <div className="tag-row">
//                 {product.matched_keywords.map((keyword) => (
//                     <span key={keyword}>{keyword}</span>
//                 ))}
//             </div>

//             <p className="product-info">
//                 <b>주요 성분</b>
//                 <br />
//                 {product.main_ingredients}
//             </p>

//             <p className="product-reason">{product.reason}</p>
//         </div>
//     );
// }

// export default ProductCard;

function ProductCard({ product }) {
    return (
        <div className="product-card">
            <p className="product-brand">{product.brand}</p>
            <h4>{product.product_name}</h4>

            <p className="product-meta">
                {product.category} · {product.capacity}
            </p>

            {product.rating && (
                <p className="product-rating">
                    평점 {product.rating} · 리뷰 {product.review_count?.toLocaleString()}개
                </p>
            )}

            <div className="keyword-row">
                {product.matched_keywords?.length > 0 && (
                    <p className="product-keywords">
                        연결 성분: {product.matched_keywords.join(", ")}
                    </p>
                )}
            </div>

            <p className="product-reason">{product.reason}</p>
        </div>
    );
}

export default ProductCard;