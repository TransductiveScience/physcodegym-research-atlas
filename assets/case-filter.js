<!-- generated-by: physcodegym-case-library-v1 -->
'use strict';
(()=> {
 const search=document.querySelector('#case-search'),domain=document.querySelector('#case-domain'),
 cf=document.querySelector('#case-cf'),count=document.querySelector('#case-result-count');
 if(!search||!domain||!cf||!count)return;
 const rows=Array.from(document.querySelectorAll('.case-row'));
 const query=new URLSearchParams(location.search);
 if(query.get('q'))search.value=query.get('q');
 if(['rigid-body','liquid','cloth','wind'].includes(query.get('domain')))domain.value=query.get('domain');
 if(['true','false'].includes(query.get('cf')))cf.value=query.get('cf');
 function filter(){
   const q=search.value.trim().toLowerCase(),d=domain.value,c=cf.value;
   let n=0;
   for(const row of rows){
     const show=(!q||row.dataset.search.includes(q))&&(d==='all'||row.dataset.category===d)&&(c==='all'||row.dataset.cf===c);
     row.hidden=!show; if(show)n++;
   }
   count.textContent=n+' of '+rows.length+' reference cases match.';
   const u=new URL(location.href);
   if(q)u.searchParams.set('q',search.value.trim());else u.searchParams.delete('q');
   if(d!=='all')u.searchParams.set('domain',d);else u.searchParams.delete('domain');
   if(c!=='all')u.searchParams.set('cf',c);else u.searchParams.delete('cf');
   history.replaceState(null,'',u.pathname+u.search+u.hash);
 }
 for(const control of [search,domain,cf])control.addEventListener('input',filter);
 filter();
})();
