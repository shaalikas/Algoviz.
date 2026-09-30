// Front page: theme toggle (shares the "av_theme" key with the app) and footer year
(function(){var t=null;try{t=JSON.parse(localStorage.getItem('av_theme'))}catch(e){}
if(t)document.documentElement.dataset.theme=t;
document.getElementById('theme').onclick=function(){var d=document.documentElement,dark=d.dataset.theme=='dark'||(!d.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches),n=dark?'light':'dark';d.dataset.theme=n;try{localStorage.setItem('av_theme',JSON.stringify(n))}catch(e){}};
document.getElementById('yr').textContent=new Date().getFullYear()})();
