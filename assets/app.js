(function(){
  var R=window.RADAR_FX||{rates:{USD:1}};var SYM={USD:"US$",BRL:"R$",AOA:"Kz",EUR:"€"};
  var LOC={USD:"pt-BR",BRL:"pt-BR",AOA:"pt-PT",EUR:"pt-PT"};
  var cur=localStorage.getItem("radar_cur")||"USD";
  function fmt(usd,c){if(usd===""||usd==null||isNaN(usd))return "—";var v=usd*R.rates[c];
    if(usd===0)return "Grátis";var d=(c==="AOA"||(c==="USD"&&usd%1===0))?0:2;
    if(c==="AOA")return SYM[c]+" "+String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g,".");
    return SYM[c]+" "+v.toLocaleString(LOC[c],{minimumFractionDigits:d,maximumFractionDigits:d});}
  function render(){document.querySelectorAll("[data-usd]").forEach(function(el){
      var u=el.getAttribute("data-usd");el.firstChild.nodeValue=fmt(u===""?null:parseFloat(u),cur);});
    document.querySelectorAll(".cur button").forEach(function(b){b.classList.toggle("on",b.dataset.c===cur);});}
  document.querySelectorAll(".cur button").forEach(function(b){b.addEventListener("click",function(){cur=b.dataset.c;localStorage.setItem("radar_cur",cur);render();});});
  render();
  var tb=document.querySelector("#cmp tbody");if(!tb)return;
  var q=document.getElementById("q"),maxp=document.getElementById("maxp"),fr=document.getElementById("freeonly"),vo=document.getElementById("veronly"),cnt=document.getElementById("count");
  function filt(){var s=(q.value||"").toLowerCase(),m=maxp.value===""?Infinity:parseFloat(maxp.value),n=0;
    tb.querySelectorAll("tr").forEach(function(tr){var p=tr.dataset.price===""?null:parseFloat(tr.dataset.price);
      var ok=tr.textContent.toLowerCase().indexOf(s)>-1&&(p===null?m===Infinity:p<=m)&&(!fr.checked||p===0)&&(!vo.checked||tr.dataset.ver==="1");
      tr.style.display=ok?"":"none";if(ok)n++;});cnt.textContent=n+" planos";}
  [q,maxp,fr,vo].forEach(function(e){e.addEventListener("input",filt);e.addEventListener("change",filt);});
  document.querySelectorAll("#cmp th[data-sort]").forEach(function(th,i){th.addEventListener("click",function(){
    var k=th.dataset.sort,asc=!th.classList.contains("asc");document.querySelectorAll("#cmp th").forEach(function(x){x.classList.remove("asc","desc");});
    th.classList.add(asc?"asc":"desc");var rows=[].slice.call(tb.querySelectorAll("tr"));
    rows.sort(function(a,b){var x=a.dataset[k],y=b.dataset[k];if(k==="price"){x=x===""?1e9:parseFloat(x);y=y===""?1e9:parseFloat(y);return asc?x-y:y-x;}
      return asc?x.localeCompare(y,"pt"):y.localeCompare(x,"pt");});rows.forEach(function(r){tb.appendChild(r);});});});
  filt();
})();

/* Newsletter (Kit): envia por fetch com Accept: application/json; sem JS, o formulário faz POST normal. */
(function(){
  document.querySelectorAll("form.kit-form").forEach(function(f){
    var msg=f.parentNode.querySelector(".news-msg"),btn=f.querySelector("button");
    function show(t,ok){msg.hidden=false;msg.textContent=t;msg.className="news-msg "+(ok?"ok":"err");}
    f.addEventListener("submit",function(e){
      if(!window.fetch||!window.FormData)return;           // recorre ao POST normal
      e.preventDefault();btn.disabled=true;var old=btn.textContent;btn.textContent="A enviar…";
      fetch(f.action,{method:"POST",body:new FormData(f),headers:{"Accept":"application/json"}})
        .then(function(r){return r.json().catch(function(){return {};}).then(function(j){return {r:r,j:j};});})
        .then(function(x){var j=x.j||{};
          if(x.r.ok&&j.status==="success"){show("✅ Quase lá! Enviámos um e-mail de confirmação. Clique no link para começar a receber o Radar às segundas.",true);f.reset();}
          else if(j.status==="quarantined"&&j.url){show("🔒 Só falta uma verificação rápida anti-spam. Vamos abrir a página de confirmação…",true);setTimeout(function(){location.href=j.url;},900);}
          else{show("⚠️ Não foi possível inscrever este e-mail. Verifique o endereço e tente de novo.",false);}
        })
        .catch(function(){f.submit();})                    // erro de rede/CORS: POST normal
        .then(function(){btn.disabled=false;btn.textContent=old;});
    });
  });
})();
