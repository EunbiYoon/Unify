// main.js
const itemsPerPage = 5; // Set the number of items per page here
let currentPage = 1;

function displayItemsForPage(pageNum) {
  const tableRows = document.querySelectorAll("#dataTable tbody tr");
  tableRows.forEach((row, index) => {
    if (index >= (pageNum - 1) * itemsPerPage && index < pageNum * itemsPerPage) {
      row.style.display = "table-row";
    } else {
      row.style.display = "none";
    }
  });
}

function updatePaginationButtons() {
  const pagination = document.getElementById("pagination");
  pagination.innerHTML = "";

  const totalItems = document.querySelectorAll("#dataTable tbody tr").length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  for (let i = 1; i <= totalPages; i++) {
    const button = document.createElement("button");
    button.innerText = i;
    button.addEventListener("click", () => {
      currentPage = i;
      displayItemsForPage(currentPage);
      updatePaginationButtons();
    });
    pagination.appendChild(button);
  }
}

function handleSearch() {
  const searchTerm = searchInput.value.toLowerCase();
  const tableRows = document.querySelectorAll("#dataTable tbody tr");

  tableRows.forEach((row) => {
    const rowData = row.innerText.toLowerCase();
    if (rowData.includes(searchTerm)) {
      row.style.display = "table-row";
    } else {
      row.style.display = "none";
    }
  });

  currentPage = 1;
  updatePaginationButtons();
}

// Event listener for search input
const searchInput = document.getElementById("searchInput");
searchInput.addEventListener("input", handleSearch);

// Function to display initial page on page load
function displayInitialPage() {
  const totalItems = document.querySelectorAll("#dataTable tbody tr").length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  updatePaginationButtons();

  // If there are multiple pages, show the first page initially
  if (totalPages > 1) {
    displayItemsForPage(currentPage);
  }
}

// Call the function on page load
displayInitialPage();
