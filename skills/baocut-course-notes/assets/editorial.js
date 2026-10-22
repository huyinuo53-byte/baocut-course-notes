const dialog=document.querySelector('dialog'),viewport=dialog.querySelector('.image-viewport'),size=document.querySelector('#actual-size');
function setActual(actual){viewport.classList.toggle('actual',actual);size.setAttribute('aria-pressed',String(actual));size.textContent=actual?'适合屏幕':'原尺寸'}
document.querySelectorAll('.zoom').forEach(button=>button.addEventListener('click',()=>{dialog.querySelector('img').src=button.querySelector('img').src;setActual(matchMedia('(max-width:600px)').matches);dialog.showModal();viewport.scrollTo(0,0)}));
size.addEventListener('click',()=>setActual(!viewport.classList.contains('actual')));
document.querySelector('#close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
let printState=[];
addEventListener('beforeprint',()=>{printState=[...document.querySelectorAll('.quiz-answer,.reading-scope,.figure-provenance')].map(el=>[el,el.open]);printState.forEach(([el])=>el.open=true)});
addEventListener('afterprint',()=>printState.forEach(([el,open])=>el.open=open));
const toc=document.querySelector('.course-toc'),wide=matchMedia('(min-width:1100px)');
function fitToc(){toc.open=wide.matches}fitToc();wide.addEventListener('change',fitToc);
toc.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{if(!wide.matches)toc.open=false}));
const links=[...toc.querySelectorAll('a')],sections=[...document.querySelectorAll('main>section')];
let scheduled=false;
function markSection(){scheduled=false;let current=sections[0];for(const section of sections){if(section.getBoundingClientRect().top<160)current=section}links.forEach(link=>{if(link.hash==='#'+current.id)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current')})}
addEventListener('scroll',()=>{if(!scheduled){scheduled=true;requestAnimationFrame(markSection)}},{passive:true});markSection();
