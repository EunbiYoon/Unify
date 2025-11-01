function copyText(element){
    var textToCopy=element.textContent.slice(0,-4);
    navigator.clipboard.writeText(textToCopy).then(function(){
        element.innerHTML='Copied!';
        setTimeout(function(){
            element.innerHTML=textToCopy+' <a>Copy</a>';
        }, 1000);
    })
    .catch(function (error){
        console.error('Unable to copy text: ',error)
    });
}