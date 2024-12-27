const inputField = document.getElementById('datetimepicker');
const outputText = document.getElementById('outdatetime');
const hiddenInput = document.getElementById('hiddenInput');

inputField.addEventListener('input', function() {
    const inputDateString=inputField.value;
    const inputDate=new Date(inputDateString);
    
    // Adjust the time if it's between 7pm and 7am
    if (inputDate.getHours() >= 19 || inputDate.getHours() < 7) {
        inputDate.setHours(inputDate.getHours() + 12);
        const formattedDate = inputDate.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: '2-digit' });
        const formattedTime = inputDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        outputText.textContent = formattedDate + ' ' + formattedTime;
        hiddenInput.value = formattedDate + ' ' + formattedTime;
    }
    else {
        outputText.textContent = "Not Applicable";
        hiddenInput.value = "Not Applicable";
    }
});