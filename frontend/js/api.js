const L={api:'API',core:'Core',adapter:'Adapter',util:'Util',ext:'External'};
const SAMPLE_REPOS={axios:'axios/axios',flask:'pallets/flask',gin:'gin-gonic/gin'};
const api={async analyze(url,zip){
 let response;
 if(zip){
  const file=window.selectedZip||document.querySelector('#zf').files[0];
  if(!file)throw new Error('Choose a .zip file first.');
  const form=new FormData();form.append('file',file);form.append('options',JSON.stringify({includeDependencies:true}));
  response=await fetch('/api/analyze/upload',{method:'POST',body:form});
 }else{
  response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,includeDependencies:true})});
 }
 const result=await response.json();
 if(!response.ok||result.success===false)throw new Error(result.error?.message||'Analysis failed.');
 return result;
}};
