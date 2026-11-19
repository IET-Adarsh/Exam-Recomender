document.addEventListener("DOMContentLoaded", function () {
    setupNavToggle();
    setupAuthTabs();
    setupFormValidation();
    setupExamFilter();
});

function setupNavToggle() {
    var button = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (!button || !links) return;
    button.addEventListener("click", function () {
        var isOpen = links.classList.toggle("open");
        button.setAttribute("aria-expanded", String(isOpen));
    });
}

function setupAuthTabs() {
    var tabBar = document.getElementById("authTabs");
    if (!tabBar) return;
    var buttons = tabBar.querySelectorAll(".tab-btn");
    var panels = document.querySelectorAll(".tab-panel");
    buttons.forEach(function (button) {
        button.addEventListener("click", function () {
            buttons.forEach(function (item) { item.classList.remove("active"); });
            panels.forEach(function (panel) { panel.classList.remove("active"); });
            button.classList.add("active");
            var panel = document.getElementById(button.dataset.tab);
            if (panel) panel.classList.add("active");
        });
    });
}

function setupFormValidation() {
    document.querySelectorAll("form[data-validate]").forEach(function (form) {
        var fields = form.querySelectorAll("input, select");
        form.addEventListener("submit", function (event) {
            var allValid = true;
            fields.forEach(function (field) {
                if (!validateField(field)) allValid = false;
            });
            if (!allValid) event.preventDefault();
        });
        fields.forEach(function (field) {
            field.addEventListener("blur", function () { validateField(field); });
            if (field.dataset.match) {
                var other = document.getElementById(field.dataset.match);
                if (other) other.addEventListener("input", function () { validateField(field); });
            }
        });
    });
}

function validateField(field) {
    var value = field.value.trim();
    var message = "";
    if (field.required && value === "") {
        message = "This field is required.";
    } else if (value !== "") {
        if (field.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            message = "Enter a valid email address.";
        } else if (field.minLength > 0 && value.length < field.minLength) {
            message = "Enter at least " + field.minLength + " characters.";
        } else if (field.type === "number") {
            var number = Number(value);
            if (!Number.isFinite(number)) {
                message = "Enter a valid number.";
            } else if (field.min !== "" && number < Number(field.min)) {
                message = "Value must be at least " + field.min + ".";
            } else if (field.max !== "" && number > Number(field.max)) {
                message = "Value must be at most " + field.max + ".";
            }
        } else if (field.type === "date" && field.max && value > field.max) {
            message = "Date cannot be in the future.";
        }
        if (!message && field.dataset.match) {
            var other = document.getElementById(field.dataset.match);
            if (other && other.value !== field.value) message = "Passwords do not match.";
        }
    }
    var row = field.closest(".form-row");
    var errorBox = row ? row.querySelector(".error-text") : null;
    if (errorBox) errorBox.textContent = message;
    if (row) row.classList.toggle("has-error", message !== "");
    return message === "";
}

function setupExamFilter() {
    var filterBar = document.getElementById("filterBar");
    if (!filterBar) return;
    var buttons = Array.from(filterBar.querySelectorAll(".filter-btn"));
    var cards = Array.from(document.querySelectorAll(".exam-card"));
    var emptyMessage = document.getElementById("emptyMessage");
    var resultCount = document.getElementById("resultCount");

    function applyFilter(category) {
        var visible = 0;
        buttons.forEach(function (button) {
            button.classList.toggle("active", button.dataset.filter === category);
        });
        cards.forEach(function (card) {
            var cardCategory = card.dataset.category || "uncategorized";
            var show = category === "all" || cardCategory === category;
            card.hidden = !show;
            if (show) visible += 1;
        });
        if (emptyMessage) emptyMessage.hidden = visible !== 0;
        if (resultCount) resultCount.textContent = visible + (visible === 1 ? " exam shown" : " exams shown");
    }

    buttons.forEach(function (button) {
        button.addEventListener("click", function () { applyFilter(button.dataset.filter); });
    });

    var selected = filterBar.dataset.selected || "all";
    var hasSelected = buttons.some(function (button) { return button.dataset.filter === selected; });
    applyFilter(hasSelected ? selected : "all");
}
