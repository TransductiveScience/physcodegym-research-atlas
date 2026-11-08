<!-- generated-by: physcodegym-case-library-v1 -->
'use strict';
(()=> {
 const search=document.querySelector('#case-search'),domain=document.querySelector('#case-domain'),
 cf=document.querySelector('#case-cf'),count=document.querySelector('#case-result-count');
 if(!search||!domain||!cf||!count)return;
 const rows=Array.from(document.querySelectorAll('.case-row'));
 function filter(){
   const q=search.value.trim().toLowerCase(),d=domain.value,c=cf.value;
   let n=0;
   for(const row of rows){
     const show=(!q||row.dataset.search.includes(q))&&(d==='all'||row.dataset.category===d)&&(c==='all'||row.dataset.cf===c);
     row.hidden=!show; if(show)n++;
   }
   count.textContent=n+' of '+rows.length+' reference cases match.';
 }
 for(const control of [search,domain,cf])control.addEventListener('input',filter);
 filter();
})();
