// current_time.js
// Function to update the current time
function updateCurrentTime() {
    var currentTimeElement = document.getElementById('current-time');
    var now = new Date();
    var month = String(now.getMonth()+1).padStart(2,'0');
    var day =  String(now.getDay()).padStart(2,'0');
    var year = String(now.getFullYear());
    var hours = String(now.getHours()).padStart(2, '0');
    var minutes = String(now.getMinutes()).padStart(2, '0');
    var seconds = String(now.getSeconds()).padStart(2, '0');
    var currentTimeString = month + '/' + day + '/' + year + ' ' +hours + ':' + minutes + ':' + seconds;
    currentTimeElement.textContent = currentTimeString;
    }

    // Update the time every second (1000 milliseconds)
    setInterval(updateCurrentTime, 1000);

    // Call the function once initially to display the time immediately
    updateCurrentTime();