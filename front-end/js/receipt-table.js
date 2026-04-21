let url = "http://localhost:5000/api";

$(document).ready(function() {
    getAllReceipts();
});

/* ───────────── LẤY DANH SÁCH PHIẾU ───────────── */
/* Sửa hàm getAllReceipts trong receipt-table.js */
function getAllReceipts() {
    $.ajax({
        url: url + "/receipts/",
        method: "GET",
        xhrFields: { withCredentials: true },
        success: function(res) {
            // Sắp xếp: Phiếu mới nhất (ID lớn nhất) lên đầu
            const list = res.sort((a, b) => b.id - a.id);
            let html = "";

            if (!list || list.length === 0) {
                html = '<tr><td colspan="8" class="text-center text-muted py-4">Không có giao dịch nào.</td></tr>';
            } else {
                list.forEach(r => {
                    const badgeClass = getBadgeClass(r.type);
                    const typeText = getTypeText(r.type);
                    const itemCount = r.items ? r.items.length : 0;

                    html += `
                    <tr>
                        <td><strong>#${r.id}</strong></td>
                        <td><span class="badge ${badgeClass}">${typeText}</span></td>
                        <td>${r.warehouse_name}</td>
                        <td>${r.staff_name}</td>
                        <td>${r.partner_name || 'N/A'}</td>
                        <td>${r.created_at}</td>
                        <td><span class="text-primary">${itemCount} mặt hàng</span></td>
                        <td>
                             <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteReceipt(${r.id})">
                                <i class="bx bx-trash me-1"></i> Xóa
                             </button>
                        </td>
                    </tr>`;
                });
            }
            $("#receiptsTableBody").html(html);
        },
        error: function(xhr) {
            if (xhr.status === 401) window.location.href = 'login.html';
            showToast("Lỗi tải danh sách phiếu", "danger");
        }
    });
}
/* ───────────── HELPER FUNCTIONS ───────────── */
function getBadgeClass(type) {
    switch (type.toUpperCase()) {
        case 'INBOUND':
            return 'bg-label-success';
        case 'OUTBOUND':
            return 'bg-label-danger';
        case 'AUDIT':
            return 'bg-label-warning';
        default:
            return 'bg-label-primary';
    }
}

function getTypeText(type) {
    switch (type.toUpperCase()) {
        case 'INBOUND':
            return 'NHẬP KHO';
        case 'OUTBOUND':
            return 'XUẤT KHO';
        case 'AUDIT':
            return 'KIỂM KÊ';
        default:
            return type;
    }
}

/* ───────────── XÓA PHIẾU ───────────── */
function confirmDeleteReceipt(id) {
    if (confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn phiếu #${id}? Hành động này không thể hoàn tác.`)) {
        $.ajax({
            url: url + "/receipts/" + id,
            method: "DELETE",
            xhrFields: { withCredentials: true },
            success: function() {
                showToast("Đã xóa phiếu thành công", "success");
                getAllReceipts(); // Tải lại bảng
            },
            error: function(xhr) {
                const msg = xhr.responseJSON ? xhr.responseJSON.message : "Không thể xóa phiếu";
                showToast(msg, "danger");
            }
        });
    }
}

function showToast(message, type = "success") {
    // Sử dụng lại hàm showToast từ productTable.js
    if (!document.getElementById("toastContainer")) {
        const container = document.createElement("div");
        container.id = "toastContainer";
        container.style.cssText = "position:fixed;top:20px;right:20px;z-index:9999;min-width:280px;";
        document.body.appendChild(container);
    }
    const id = "toast_" + Date.now();
    const bg = type === "success" ? "bg-success" : "bg-danger";

    document.getElementById("toastContainer").insertAdjacentHTML("beforeend", `
        <div id="${id}" class="toast show align-items-center text-white ${bg} border-0 mb-2" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        </div>`);
    setTimeout(() => { $(`#${id}`).fadeOut(() => $(`#${id}`).remove()); }, 3000);
}