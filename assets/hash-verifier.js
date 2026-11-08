// generated-by: transductive-physics-verifier-v1
'use strict';
(()=>{
 const caseEl=document.querySelector('#hash-case'),fileEl=document.querySelector('#hash-file'),button=document.querySelector('#hash-run');
 const expected=document.querySelector('#hash-expected'),observed=document.querySelector('#hash-observed');
 const bytes=document.querySelector('#hash-bytes'),filename=document.querySelector('#hash-name'),status=document.querySelector('#hash-status');
 if(!caseEl||!fileEl||!button)return;
 const params=new URLSearchParams(location.search),want=params.get('case');
 if(want && Array.from(caseEl.options).some(o=>o.value===want))caseEl.value=want;
 function refresh(){
   const o=caseEl.selectedOptions[0];expected.textContent=o.dataset.sha;
   bytes.textContent=Number(o.dataset.size).toLocaleString('en-US');
   status.textContent='Ready to verify a local reference MP4.';
   observed.textContent='Not calculated.';
   filename.textContent=fileEl.files[0]?.name||'None';
 }
 caseEl.addEventListener('change',refresh);
 fileEl.addEventListener('change',refresh);
 button.addEventListener('click',async ()=>{
   const file=fileEl.files[0],option=caseEl.selectedOptions[0];
   if(!file){status.textContent='Choose a file first.';return;}
   if(!window.crypto?.subtle){status.textContent='Cryptographic hashing unavailable; use an HTTPS connection.';return;}
   button.disabled=true;status.textContent='Reading and hashing locally…';observed.textContent='Computing…';
   try{
     const buffer=await file.arrayBuffer();
     const digest=await crypto.subtle.digest('SHA-256',buffer);
     const actual=Array.from(new Uint8Array(digest)).map(b=>b.toString(16).padStart(2,'0')).join('');
     observed.textContent=actual;
     const sizeOK=file.size===Number(option.dataset.size);
     const match=actual===option.dataset.sha.toLowerCase();
     status.textContent=match?'MATCH: Exact published reference bytes.':('MISMATCH: The file differs from the reference. '+(sizeOK?'Size matches but SHA-256 differs.':'File size differs.'));
     status.dataset.match=match?'yes':'no';
   }catch(e){status.textContent='Local verification failed: '+(e?.message||'Unknown error');}
   finally{button.disabled=false;}
 });
 refresh();
})();
