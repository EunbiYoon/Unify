/*!
    * Start Bootstrap - SB Admin v7.0.5 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2022 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});
function doDark(){
    alert("Dark Color Theme Has been Changed");
    const topnav = document.getElementById("topnav"); // div element
    const sidenav = document.getElementById("sidenavAccordion"); // div element
    topnav.className="sb-topnav navbar navbar-expand navbar-dark bg-dark";
    sidenav.className="sb-sidenav accordion sb-sidenav-dark";
}

function doLight(){
    alert("Light Color Theme Has been Changed");
    const topnav = document.getElementById("topnav"); // div element
    const sidenav = document.getElementById("sidenavAccordion"); // div element
    topnav.className="sb-topnav navbar navbar-expand navbar-light bg-light";
    sidenav.className="sb-sidenav accordion sb-sidenav-light";
}