function genQR(){
    var gapi="https://chart.googleapis.com/chart?cht=qr&chs=";

    // edit the qr code information
    var myimg=document.getElementById("img");
    var mytext=document.getElementById("qrtext").value;
    var mysize=document.getElementById("size").value;

    // check textarea
    if (mytext!=="" && mysize=="100")
    {
        myimg.src=gapi+"100x100"+"&chl="+mytext
    }
    else if (mytext!=="" && mysize=="150")
    {
        myimg.src=gapi+"150x150"+"&chl="+mytext
    }
    else if (mytext!=="" && mysize=="200")
    {
        myimg.src=gapi+"200x200"+"&chl="+mytext
    }
    else if (mytext!=="" && mysize=="250")
    {
        myimg.src=gapi+"250x250"+"&chl="+mytext
    }
    else if (mytext!=="" && mysize=="300")
    {
        myimg.src=gapi+"300x300"+"&chl="+mytext
    }
    // textarea empty
    else
    {
        alert("Please Enter Text");
    }}