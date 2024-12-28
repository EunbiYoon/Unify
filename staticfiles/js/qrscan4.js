document.addEventListener('DOMContentLoaded', function(){
    const scanner= new Html5QrcodeScanner(
        'reader',{
        qrbox:{
            width:250,
            height:250,
        },
        fps:20,
    });
    scanner.render(success);
});

function success(result) {
    /*change reader to success message*/ 
    var reader=document.getElementById('result')
    reader.innerHTML = `${result}`;

    var typemanually=document.getElementById('reader')
    typemanually.innerHTML="";
    
    var newText = document.getElementById("typetext");
    newText.innerHTML='If the tracking number is not correct, then refresh page and type manually'
   
}
function error(err){
    console.error(err);
}

