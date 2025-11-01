document.addEventListener("DOMContentLoaded", function () {
    // ✅ Select2 적용 (태그형 입력 가능)
    if (typeof $ !== "undefined" && $.fn.select2) {
        $('.select2').select2({
            tags: true,
            width: 'resolve',
            placeholder: "태그를 입력하거나 선택하세요"
        });
    }
});
