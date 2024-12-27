function filterTable() {
    var input, filter, table, tr, td, i;
    input = document.getElementById("filterInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");

    // Loop through all table rows, and hide those that don't match the filter
    for (i = 1; i < tr.length; i++) {
        var match = false;
        for (var j = 0; j < tr[i].cells.length; j++) {
        td = tr[i].getElementsByTagName("td")[j];
        if (td) {
            if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
            match = true;
            break;
            }
        }
        }
        if (match) {
        tr[i].style.display = "";
        } else {
        tr[i].style.display = "none";
        }
    }
}

const myInput = document.getElementById("myInput");
myInput.addEventListener("input",function(){
    if(myInput.value===""){
        myInput.classList.add("blank");
    }
    else{
        myInput.classList.remove("blank");
    }
});