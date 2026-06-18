// Trang base.html
// document.addEventListener("DOMContentLoaded", function() {
//     let cartBadge = document.getElementById("cart-count");
//     if(cartBadge){
//         fetch("/api/cart/count")
//             .then(res => res.json())
//             .then(data => {
//             cartBadge.innerText = data.count;
//         })
//         .catch(error => console.error("Lỗi cập nhật giỏ hàng:", error));
//     }
// });
// Cart thêm bớt sản phẩm trong giỏ hàng
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.js-btn-plus').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.getAttribute('data-item-id');
            const inputField = document.getElementById(`qty-${itemId}`);
            let currentQty = parseInt(inputField.value);
            currentQty += 1;
            inputField.value = currentQty;
            sendUpdateCart(itemId, currentQty);
        });
    });
    document.querySelectorAll('.js-btn-minus').forEach(button => {
        button.addEventListener('click', function(){
            const itemId = this.getAttribute('data-item-id');
            const inputField = document.getElementById(`qty-${itemId}`);
            let currentQty = parseInt(inputField.value);
            if(currentQty > 1){
                currentQty -= 1;
                inputField.value = currentQty;
                sendUpdateCart(itemId, currentQty);
            }
        });
    });
    document.querySelectorAll('.qty-box').forEach(inputField => {
        inputField.addEventListener('change', function(){
            const itemId = this.id.replace('qty-', '');
            let currentQty = parseInt(this.value);
            if(isNaN(currentQty) || currentQty < 1){
                currentQty = 1;
                this.value = 1;
            }
            sendUpdateCart(itemId, currentQty);
        });
    });
    function sendUpdateCart(itemId, newQty){
        fetch(`/api/cart/update/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({quantity: newQty})
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                // 1. Nếu có tin nhắn cảnh báo (do bị ép số), hiện lên cho khách biết
                if (data.message) {
                    alert(data.message);
                }

                // 2. Lấy con số chính thức mà Server vừa chốt
                const finalQty = data.updated_qty !== undefined ? data.updated_qty : newQty;

                // 3. Ép lại ô input trên màn hình về đúng con số chuẩn
                const inputField = document.getElementById(`qty-${itemId}`);
                if (inputField) {
                    inputField.value = finalQty;
                }

                // 4. Cập nhật THÀNH TIỀN của món hàng đó
                const price = parseFloat(inputField.getAttribute('data-price'));
                const lineTotal = price * finalQty;
                const lineTotalElem = document.getElementById(`total-price-${itemId}`);
                if(lineTotalElem){
                    lineTotalElem.innerText = lineTotal.toLocaleString('vi-VN') + ' ₫';
                }

                // 5. Cập nhật TỔNG TIỀN thanh toán bên dưới
                const totalCartElem = document.getElementById('cart-total-amount');
                if(totalCartElem && data.new_total_amount !== undefined){
                    totalCartElem.innerText = data.new_total_amount.toLocaleString('vi-VN') + ' ₫';
                }

                // 6. Cập nhật TỔNG SẢN PHẨM (cái chữ "4 sản phẩm" của bạn sẽ nhảy đúng)
                const cartBadge = document.getElementById("cart-count");
                if(cartBadge && data.cart_count !== undefined){
                    cartBadge.innerText = data.cart_count;
                }
                const totalQuantityDisplay = document.getElementById("total-quantity-display"); 
                if(totalQuantityDisplay && data.cart_count !== undefined){
                    totalQuantityDisplay.innerText = data.cart_count; 
                }

            } else {
                // Lỗi này giờ chỉ dành cho các ca nghiêm trọng (ví dụ: mất đăng nhập, lỗi hệ thống)
                alert("Lỗi: " + data.message);
            }
        })
        .catch(err => console.error("Lỗi Fetch:", err));
    }
});

// Trang index.html
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("search-input");
    const searchResults = document.getElementById("search-results");

    if (searchInput && searchResults) {
        searchInput.addEventListener("input", function() {
            const query = this.value.trim();

            // Nếu người dùng xóa hết chữ, ẩn ngay khung kết quả
            if (query.length === 0) {
                searchResults.style.display = "none";
                searchResults.innerHTML = "";
                return;
            }

            // Gọi API ngầm lên Flask Backend để lấy sản phẩm khớp từ khóa
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(products => {
                    if (products.length === 0) {
                        // Nếu không tìm thấy sản phẩm nào khớp
                        searchResults.innerHTML = `<div class="dropdown-item text-muted small py-2">Không tìm thấy sản phẩm nào...</div>`;
                    } else {
                        // Nếu có sản phẩm, lặp qua và vẽ HTML hiển thị dạng danh sách có ảnh nhỏ và giá tiền
                        let htmlContent = "";
                        products.forEach(p => {
                            htmlContent += `
                                <a href="/product_id/${p.id}" class="dropdown-item d-flex align-items-center py-2 border-bottom" style="gap: 10px;">
                                    
                                    <img src="/static/uploads/${p.image_url}" alt="${p.name}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 4px;">
                                    
                                    <div style="white-space: normal;">
                                        <div class="fw-semibold text-dark small mb-0" style="line-height: 1.2;">${p.name}</div>
                                        <small class="text-primary fw-bold">${p.price}</small>
                                    </div>
                                </a>
                            `;
                        });
                        searchResults.innerHTML = htmlContent;
                    }
                    // Hiện khung dropdown kết quả lên màn hình
                    searchResults.style.display = "block";
                })
                .catch(err => console.error("Lỗi tìm kiếm:", err));
        });

        // Tự động đóng khung tìm kiếm nếu người dùng click chuột ra ngoài khu vực ô tìm kiếm
        document.addEventListener("click", function(event) {
            if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
                searchResults.style.display = "none";
            }
        });
    }
});

// Trang xem chi tiết sản phẩm (product_detail.html)
function validateQty() {
    let input = document.getElementById("quantity-input");
    let currentVal = parseInt(input.value);
    
    if (isNaN(currentVal) || currentVal < 1) {
        input.value = 1;
    } else if (currentVal > maxStock) {
        input.value = maxStock;
    }
}

function addToCart(productId) {
    let quantity = 1;
    let qtyInput = document.getElementById("quantity-input");
    if (qtyInput) {
        quantity = parseInt(qtyInput.value);
    }

    fetch(`/api/cart/add/${productId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ quantity: quantity })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById("cart-count").innerText = data.cart_count;
        } else {
            alert(data.message || "Có lỗi xảy ra!");
        }
    })
    .catch(error => {
        console.error("Lỗi:", error);
    });
}