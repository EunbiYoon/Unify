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
    var reader=document.getElementById('reader')
    reader.innerHTML = ``;
    document.getElementById('choose').innerHTML = ``;
    
    /*change reader to success message*/
    document.getElementById('info').innerHTML = ``;

    /*change value*/
    var input=document.getElementById("result");
    input.value=result;

    /* remove the border*/
    reader.style.border='none';

    /* reshape and make border*/
    reader.style.border='none';
    input.style.borderRadius='15px';

    /* cleanup the scanner*/
    scanner.clear();
    // document.getElementById('reader').innerHTML = `
    // <h2>Success!</h2>
    // <p><a href="${result}">${result}</a></p>
    // `;
}
function error(err){
    console.error(err);
}

