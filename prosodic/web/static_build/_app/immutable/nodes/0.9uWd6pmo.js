import"../chunks/Bzak7iHL.js";import{x as Nt,E as ga,aO as ma,A as Q,J as Ke,ax as at,F as vt,g as n,H as Ja,ah as Ka,I as la,K as st,B as je,aF as xa,aM as Za,ap as ia,z as He,aP as Pe,y as St,aQ as Xa,D as Qa,a6 as es,aR as wa,aL as Zt,aS as ts,aT as as,a9 as ss,Q as oa,aU as ns,a1 as rs,n as $a,v as ya,aV as Ht,af as ka,aW as ls,aX as is,aJ as os,C as cs,q as Wt,aG as Ta,t as K,O as za,aY as vs,aN as us,aH as ds,aw as Ca,aZ as Ea,a_ as fs,a$ as ps,G as _s,b0 as Sa,b1 as Aa,M as Xt,b2 as Qt,b3 as bs,b4 as hs,b5 as gs,b6 as ms,b7 as Mt,b8 as xs,b9 as ws,ba as $s,bb as ys,bc as ks,bd as Ts,be as zs,aa as Cs,e as ee,N as La,p as Ne,k as v,j as fe,m as i,l as o,a as qe,h as ct,ac as Se,bf as ea,s as Oe,b as ce,bg as J,bh as Es,d as ta,$ as S,ab as ae,aq as Ss,o as Ma,_ as aa,bi as ke}from"../chunks/BPpoBFJ_.js";import{b as qt,i as As,d as Ls,e as U,g as We,j as Ms,n as Ps,k as Ns,a as T,f as F,c as ze,l as qs,s as I,t as Yt}from"../chunks/Dj5n7Ctz.js";import{B as Os,l as Xe,p as Ce,s as pt,i as se,b as ca,c as va}from"../chunks/DHdWuXdj.js";import"../chunks/69_IOA4Y.js";import{i as Pa,a as Ct,b as At,z as ut,m as Ee,c as Ze,s as De,d as Je,e as ua,g as Rt,p as jt,f as Ot,h as Na,j as qa,k as Oa,l as wt,n as $t}from"../chunks/CVpnQTwf.js";function Ve(e,t){return t}function Ws(e,t,a){for(var s=[],l=t.length,c,r=t.length,u=0;u<l;u++){let m=t[u];ya(m,()=>{if(c){if(c.pending.delete(m),c.done.add(m),c.pending.size===0){var p=e.outrogroups;Jt(e,Zt(c.done)),p.delete(c),p.size===0&&(e.outrogroups=null)}}else r-=1},!1)}if(r===0){var f=s.length===0&&a!==null;if(f){var _=a,d=_.parentNode;os(d),d.append(_),e.items.clear()}Jt(e,t,!f)}else c={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(c)}function Jt(e,t,a=!0){var s;if(e.pending.size>0){s=new Set;for(const r of e.pending.values())for(const u of r)s.add(e.items.get(u).e)}for(var l=0;l<t.length;l++){var c=t[l];if(s!=null&&s.has(c)){c.f|=Pe;const r=document.createDocumentFragment();cs(c,r)}else Wt(t[l],a)}}var da;function Te(e,t,a,s,l,c=null){var r=e,u=new Map,f=(t&ma)!==0;if(f){var _=e;r=Q?Ke(at(_)):_.appendChild(Nt())}Q&&vt();var d=null,m=es(()=>{var M=a();return wa(M)?M:M==null?[]:Zt(M)}),p,x=new Map,$=!0;function N(M){(D.effect.f&rs)===0&&(D.pending.delete(M),D.fallback=d,Rs(D,p,r,t,s),d!==null&&(p.length===0?(d.f&Pe)===0?$a(d):(d.f^=Pe,zt(d,null,r)):ya(d,()=>{d=null})))}function b(M){D.pending.delete(M)}var h=ga(()=>{p=n(m);var M=p.length;let k=!1;if(Q){var Y=Ja(r)===Ka;Y!==(M===0)&&(r=la(),Ke(r),st(!1),k=!0)}for(var C=new Set,E=He,R=Qa(),z=0;z<M;z+=1){Q&&je.nodeType===xa&&je.data===Za&&(r=je,k=!0,st(!1));var q=p[z],j=s(q,z),L=$?null:u.get(j);L?(L.v&&ia(L.v,q),L.i&&ia(L.i,z),R&&E.unskip_effect(L.e)):(L=Is(u,$?r:da??(da=Nt()),q,j,z,l,t,a),$||(L.e.f|=Pe),u.set(j,L)),C.add(j)}if(M===0&&c&&!d&&($?d=St(()=>c(r)):(d=St(()=>c(da??(da=Nt()))),d.f|=Pe)),M>C.size&&Xa(),Q&&M>0&&Ke(la()),!$)if(x.set(E,C),R){for(const[X,P]of u)C.has(X)||E.skip_effect(P.e);E.oncommit(N),E.ondiscard(b)}else N(E);k&&st(!0),n(m)}),D={effect:h,items:u,pending:x,outrogroups:null,fallback:d};$=!1,Q&&(r=je)}function yt(e){for(;e!==null&&(e.f&ls)===0;)e=e.next;return e}function Rs(e,t,a,s,l){var q,j,L,X,P,B,w,y,O;var c=(s&is)!==0,r=t.length,u=e.items,f=yt(e.effect.first),_,d=null,m,p=[],x=[],$,N,b,h;if(c)for(h=0;h<r;h+=1)$=t[h],N=l($,h),b=u.get(N).e,(b.f&Pe)===0&&((j=(q=b.nodes)==null?void 0:q.a)==null||j.measure(),(m??(m=new Set)).add(b));for(h=0;h<r;h+=1){if($=t[h],N=l($,h),b=u.get(N).e,e.outrogroups!==null)for(const g of e.outrogroups)g.pending.delete(b),g.done.delete(b);if((b.f&Ht)!==0&&($a(b),c&&((X=(L=b.nodes)==null?void 0:L.a)==null||X.unfix(),(m??(m=new Set)).delete(b))),(b.f&Pe)!==0)if(b.f^=Pe,b===f)zt(b,null,a);else{var D=d?d.next:f;b===e.effect.last&&(e.effect.last=b.prev),b.prev&&(b.prev.next=b.next),b.next&&(b.next.prev=b.prev),Ye(e,d,b),Ye(e,b,D),zt(b,D,a),d=b,p=[],x=[],f=yt(d.next);continue}if(b!==f){if(_!==void 0&&_.has(b)){if(p.length<x.length){var M=x[0],k;d=M.prev;var Y=p[0],C=p[p.length-1];for(k=0;k<p.length;k+=1)zt(p[k],M,a);for(k=0;k<x.length;k+=1)_.delete(x[k]);Ye(e,Y.prev,C.next),Ye(e,d,Y),Ye(e,C,M),f=M,d=C,h-=1,p=[],x=[]}else _.delete(b),zt(b,f,a),Ye(e,b.prev,b.next),Ye(e,b,d===null?e.effect.first:d.next),Ye(e,d,b),d=b;continue}for(p=[],x=[];f!==null&&f!==b;)(_??(_=new Set)).add(f),x.push(f),f=yt(f.next);if(f===null)continue}(b.f&Pe)===0&&p.push(b),d=b,f=yt(b.next)}if(e.outrogroups!==null){for(const g of e.outrogroups)g.pending.size===0&&(Jt(e,Zt(g.done)),(P=e.outrogroups)==null||P.delete(g));e.outrogroups.size===0&&(e.outrogroups=null)}if(f!==null||_!==void 0){var E=[];if(_!==void 0)for(b of _)(b.f&Ht)===0&&E.push(b);for(;f!==null;)(f.f&Ht)===0&&f!==e.fallback&&E.push(f),f=yt(f.next);var R=E.length;if(R>0){var z=(s&ma)!==0&&r===0?a:null;if(c){for(h=0;h<R;h+=1)(w=(B=E[h].nodes)==null?void 0:B.a)==null||w.measure();for(h=0;h<R;h+=1)(O=(y=E[h].nodes)==null?void 0:y.a)==null||O.fix()}Ws(e,E,z)}}c&&ka(()=>{var g,W;if(m!==void 0)for(b of m)(W=(g=b.nodes)==null?void 0:g.a)==null||W.apply()})}function Is(e,t,a,s,l,c,r,u){var f=(r&ts)!==0?(r&as)===0?ss(a,!1,!1):oa(a):null,_=(r&ns)!==0?oa(l):null;return{v:f,i:_,e:St(()=>(c(t,f??a,_??l,u),()=>{e.delete(s)}))}}function zt(e,t,a){if(e.nodes)for(var s=e.nodes.start,l=e.nodes.end,c=t&&(t.f&Pe)===0?t.nodes.start:a;s!==null;){var r=Ta(s);if(c.before(s),s===l)return;s=r}}function Ye(e,t,a){t===null?e.effect.first=a:t.next=a,a===null?e.effect.last=t:a.prev=t}function Kt(e,t,a=!1,s=!1,l=!1,c=!1){var r=e,u="";if(a){var f=e;Q&&(r=Ke(at(f)))}K(()=>{var _=za;if(u===(u=t()??"")){Q&&vt();return}if(a&&!Q){_.nodes=null,f.innerHTML=u,u!==""&&qt(at(f),f.lastChild);return}if(_.nodes!==null&&(vs(_.nodes.start,_.nodes.end),_.nodes=null),u!==""){if(Q){je.data;for(var d=vt(),m=d;d!==null&&(d.nodeType!==xa||d.data!=="");)m=d,d=Ta(d);if(d===null)throw us(),ds;qt(je,m),r=Ke(d);return}var p=s?Ea:l?fs:void 0,x=Ca(s?"svg":l?"math":"template",p);x.innerHTML=u;var $=s||l?x:x.content;if(qt(at($),$.lastChild),s||l)for(;at($);)r.before(at($));else r.before($)}})}function nt(e,t,a,s,l){var u;Q&&vt();var c=(u=t.$$slots)==null?void 0:u[a],r=!1;c===!0&&(c=t.children,r=!0),c===void 0||c(e,r?()=>s:s)}function Fs(e,t,a,s,l,c){let r=Q;Q&&vt();var u=null;Q&&je.nodeType===ps&&(u=je,vt());var f=Q?je:e,_=new Os(f,!1);ga(()=>{const d=t()||null;var m=Ea;if(d===null){_.ensure(null,null);return}return _.ensure(d,p=>{if(d){if(u=Q?u:Ca(d,m),qt(u,u),s){Q&&As(d)&&u.append(document.createComment(""));var x=Q?at(u):u.appendChild(Nt());Q&&(x===null?st(!1):Ke(x)),s(u,x)}za.nodes.end=u,p.before(u)}Q&&Ke(p)}),()=>{}},_s),Sa(()=>{}),r&&(st(!0),Ke(f))}function Ds(e,t){var a=void 0,s;Aa(()=>{a!==(a=t())&&(s&&(Wt(s),s=null),a&&(s=St(()=>{Xt(()=>a(e))})))})}function Wa(e){var t,a,s="";if(typeof e=="string"||typeof e=="number")s+=e;else if(typeof e=="object")if(Array.isArray(e)){var l=e.length;for(t=0;t<l;t++)e[t]&&(a=Wa(e[t]))&&(s&&(s+=" "),s+=a)}else for(a in e)e[a]&&(s&&(s+=" "),s+=a);return s}function Hs(){for(var e,t,a=0,s="",l=arguments.length;a<l;a++)(e=arguments[a])&&(t=Wa(e))&&(s&&(s+=" "),s+=t);return s}function js(e){return typeof e=="object"?Hs(e):e??""}const fa=[...` 	
\r\f \v\uFEFF`];function Vs(e,t,a){var s=e==null?"":""+e;if(t&&(s=s?s+" "+t:t),a){for(var l of Object.keys(a))if(a[l])s=s?s+" "+l:l;else if(s.length)for(var c=l.length,r=0;(r=s.indexOf(l,r))>=0;){var u=r+c;(r===0||fa.includes(s[r-1]))&&(u===s.length||fa.includes(s[u]))?s=(r===0?"":s.substring(0,r))+s.substring(u+1):r=u}}return s===""?null:s}function pa(e,t=!1){var a=t?" !important;":";",s="";for(var l of Object.keys(e)){var c=e[l];c!=null&&c!==""&&(s+=" "+l+": "+c+a)}return s}function Vt(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Bs(e,t){if(t){var a="",s,l;if(Array.isArray(t)?(s=t[0],l=t[1]):s=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var c=!1,r=0,u=!1,f=[];s&&f.push(...Object.keys(s).map(Vt)),l&&f.push(...Object.keys(l).map(Vt));var _=0,d=-1;const N=e.length;for(var m=0;m<N;m++){var p=e[m];if(u?p==="/"&&e[m-1]==="*"&&(u=!1):c?c===p&&(c=!1):p==="/"&&e[m+1]==="*"?u=!0:p==='"'||p==="'"?c=p:p==="("?r++:p===")"&&r--,!u&&c===!1&&r===0){if(p===":"&&d===-1)d=m;else if(p===";"||m===N-1){if(d!==-1){var x=Vt(e.substring(_,d).trim());if(!f.includes(x)){p!==";"&&m++;var $=e.substring(_,m).trim();a+=" "+$+";"}}_=m+1,d=-1}}}}return s&&(a+=pa(s)),l&&(a+=pa(l,!0)),a=a.trim(),a===""?null:a}return e==null?null:String(e)}function he(e,t,a,s,l,c){var r=e.__className;if(Q||r!==a||r===void 0){var u=Vs(a,s,c);(!Q||u!==e.getAttribute("class"))&&(u==null?e.removeAttribute("class"):t?e.className=u:e.setAttribute("class",u)),e.__className=a}else if(c&&l!==c)for(var f in c){var _=!!c[f];(l==null||_!==!!l[f])&&e.classList.toggle(f,_)}return c}function Bt(e,t={},a,s){for(var l in a){var c=a[l];t[l]!==c&&(a[l]==null?e.style.removeProperty(l):e.style.setProperty(l,c,s))}}function sa(e,t,a,s){var l=e.__style;if(Q||l!==t){var c=Bs(t,s);(!Q||c!==e.getAttribute("style"))&&(c==null?e.removeAttribute("style"):e.style.cssText=c),e.__style=t}else s&&(Array.isArray(s)?(Bt(e,a==null?void 0:a[0],s[0]),Bt(e,a==null?void 0:a[1],s[1],"important")):Bt(e,a,s));return s}function It(e,t,a=!1){if(e.multiple){if(t==null)return;if(!wa(t))return bs();for(var s of e.options)s.selected=t.includes(Et(s));return}for(s of e.options){var l=Et(s);if(hs(l,t)){s.selected=!0;return}}(!a||t!==void 0)&&(e.selectedIndex=-1)}function Ra(e){var t=new MutationObserver(()=>{It(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Sa(()=>{t.disconnect()})}function dt(e,t,a=t){var s=new WeakSet,l=!0;Qt(e,"change",c=>{var r=c?"[selected]":":checked",u;if(e.multiple)u=[].map.call(e.querySelectorAll(r),Et);else{var f=e.querySelector(r)??e.querySelector("option:not([disabled])");u=f&&Et(f)}a(u),e.__value=u,He!==null&&s.add(He)}),Xt(()=>{var c=t();if(e===document.activeElement){var r=He;if(s.has(r))return}if(It(e,c,l),l&&c===void 0){var u=e.querySelector(":checked");u!==null&&(c=Et(u),a(c))}e.__value=c,l=!1}),Ra(e)}function Et(e){return"__value"in e?e.__value:e.value}const kt=Symbol("class"),Tt=Symbol("style"),Ia=Symbol("is custom element"),Fa=Symbol("is html"),Gs=Mt?"link":"LINK",Us=Mt?"input":"INPUT",Ys=Mt?"option":"OPTION",Js=Mt?"select":"SELECT",Ks=Mt?"progress":"PROGRESS";function Ae(e){if(Q){var t=!1,a=()=>{if(!t){if(t=!0,e.hasAttribute("value")){var s=e.value;Lt(e,"value",null),e.value=s}if(e.hasAttribute("checked")){var l=e.checked;Lt(e,"checked",null),e.checked=l}}};e.__on_r=a,ka(a),$s()}}function Zs(e,t){var a=Ft(e);a.value===(a.value=t??void 0)||e.value===t&&(t!==0||e.nodeName!==Ks)||(e.value=t??"")}function Xs(e,t){var a=Ft(e);a.checked!==(a.checked=t??void 0)&&(e.checked=t)}function Qs(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Lt(e,t,a,s){var l=Ft(e);Q&&(l[t]=e.getAttribute(t),t==="src"||t==="srcset"||t==="href"&&e.nodeName===Gs)||l[t]!==(l[t]=a)&&(t==="loading"&&(e[Ts]=a),a==null?e.removeAttribute(t):typeof a!="string"&&Da(e).includes(t)?e[t]=a:e.setAttribute(t,a))}function en(e,t,a,s,l=!1,c=!1){if(Q&&l&&e.nodeName===Us){var r=e,u=r.type==="checkbox"?"defaultChecked":"defaultValue";u in a||Ae(r)}var f=Ft(e),_=f[Ia],d=!f[Fa];let m=Q&&_;m&&st(!1);var p=t||{},x=e.nodeName===Ys;for(var $ in t)$ in a||(a[$]=null);a.class?a.class=js(a.class):a[kt]&&(a.class=null),a[Tt]&&(a.style??(a.style=null));var N=Da(e);for(const C in a){let E=a[C];if(x&&C==="value"&&E==null){e.value=e.__value="",p[C]=E;continue}if(C==="class"){var b=e.namespaceURI==="http://www.w3.org/1999/xhtml";he(e,b,E,s,t==null?void 0:t[kt],a[kt]),p[C]=E,p[kt]=a[kt];continue}if(C==="style"){sa(e,E,t==null?void 0:t[Tt],a[Tt]),p[C]=E,p[Tt]=a[Tt];continue}var h=p[C];if(!(E===h&&!(E===void 0&&e.hasAttribute(C)))){p[C]=E;var D=C[0]+C[1];if(D!=="$$")if(D==="on"){const R={},z="$$"+C;let q=C.slice(2);var M=Ns(q);if(Ls(q)&&(q=q.slice(0,-7),R.capture=!0),!M&&h){if(E!=null)continue;e.removeEventListener(q,p[z],R),p[z]=null}if(M)U(q,e,E),We([q]);else if(E!=null){let j=function(L){p[C].call(this,L)};p[z]=Ms(q,e,j,R)}}else if(C==="style")Lt(e,C,E);else if(C==="autofocus")xs(e,!!E);else if(!_&&(C==="__value"||C==="value"&&E!=null))e.value=e.__value=E;else if(C==="selected"&&x)Qs(e,E);else{var k=C;d||(k=Ps(k));var Y=k==="defaultValue"||k==="defaultChecked";if(E==null&&!_&&!Y)if(f[C]=null,k==="value"||k==="checked"){let R=e;const z=t===void 0;if(k==="value"){let q=R.defaultValue;R.removeAttribute(k),R.defaultValue=q,R.value=R.__value=z?q:null}else{let q=R.defaultChecked;R.removeAttribute(k),R.defaultChecked=q,R.checked=z?q:!1}}else e.removeAttribute(C);else Y||N.includes(k)&&(_||typeof E!="string")?(e[k]=E,k in f&&(f[k]=ws)):typeof E!="function"&&Lt(e,k,E)}}}return m&&st(!0),p}function _a(e,t,a=[],s=[],l=[],c,r=!1,u=!1){gs(l,a,s,f=>{var _=void 0,d={},m=e.nodeName===Js,p=!1;if(Aa(()=>{var $=t(...f.map(n)),N=en(e,_,$,c,r,u);p&&m&&"value"in $&&It(e,$.value);for(let h of Object.getOwnPropertySymbols(d))$[h]||Wt(d[h]);for(let h of Object.getOwnPropertySymbols($)){var b=$[h];h.description===ms&&(!_||b!==_[h])&&(d[h]&&Wt(d[h]),d[h]=St(()=>Ds(e,()=>b))),N[h]=b}_=N}),m){var x=e;Xt(()=>{It(x,_.value,!0),Ra(x)})}p=!0})}function Ft(e){return e.__attributes??(e.__attributes={[Ia]:e.nodeName.includes("-"),[Fa]:e.namespaceURI===ys})}var ba=new Map;function Da(e){var t=e.getAttribute("is")||e.nodeName,a=ba.get(t);if(a)return a;ba.set(t,a=[]);for(var s,l=e,c=Element.prototype;c!==l;){s=zs(l);for(var r in s)s[r].set&&a.push(r);l=ks(l)}return a}function ft(e,t,a=t){var s=new WeakSet;Qt(e,"input",async l=>{var c=l?e.defaultValue:e.value;if(c=Gt(e)?Ut(c):c,a(c),He!==null&&s.add(He),await Cs(),c!==(c=t())){var r=e.selectionStart,u=e.selectionEnd,f=e.value.length;if(e.value=c??"",u!==null){var _=e.value.length;r===u&&u===f&&_>f?(e.selectionStart=_,e.selectionEnd=_):(e.selectionStart=r,e.selectionEnd=Math.min(u,_))}}}),(Q&&e.defaultValue!==e.value||ee(t)==null&&e.value)&&(a(Gt(e)?Ut(e.value):e.value),He!==null&&s.add(He)),La(()=>{var l=t();if(e===document.activeElement){var c=He;if(s.has(c))return}Gt(e)&&l===Ut(e.value)||e.type==="date"&&!l&&!e.value||l!==e.value&&(e.value=l??"")})}function na(e,t,a=t){Qt(e,"change",s=>{var l=s?e.defaultChecked:e.checked;a(l)}),(Q&&e.defaultChecked!==e.checked||ee(t)==null)&&a(e.checked),La(()=>{var s=t();e.checked=!!s})}function Gt(e){var t=e.type;return t==="number"||t==="range"}function Ut(e){return e===""?null:+e}const tn=!1,an=!1,kr=Object.freeze(Object.defineProperty({__proto__:null,prerender:tn,ssr:an},Symbol.toStringTag,{value:"Module"}));var sn=F(`<header class="svelte-1elxaub"><h1 class="svelte-1elxaub"><a href="https://github.com/quadrismegistus/prosodic">Prosodic</a> <span class="ipa svelte-1elxaub">[prə.'sɑ.dɪk]</span></h1> <p class="subtitle svelte-1elxaub">A metrical parser for English and Finnish</p></header>`);function nn(e){var t=sn();T(e,t)}/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const rn={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const ln=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const ha=(...e)=>e.filter((t,a,s)=>!!t&&t.trim()!==""&&s.indexOf(t)===a).join(" ").trim();var on=qs("<svg><!><!></svg>");function _t(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]),s=Xe(a,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Ne(t,!1);let l=Ce(t,"name",8,void 0),c=Ce(t,"color",8,"currentColor"),r=Ce(t,"size",8,24),u=Ce(t,"strokeWidth",8,2),f=Ce(t,"absoluteStrokeWidth",8,!1),_=Ce(t,"iconNode",24,()=>[]);Pa();var d=on();_a(d,(x,$,N)=>({...rn,...x,...s,width:r(),height:r(),stroke:c(),"stroke-width":$,class:N}),[()=>ln(s)?void 0:{"aria-hidden":"true"},()=>(ct(f()),ct(u()),ct(r()),ee(()=>f()?Number(u())*24/Number(r()):u())),()=>(ct(ha),ct(l()),ct(a),ee(()=>ha("lucide-icon","lucide",l()?`lucide-${l()}`:"",a.class)))]);var m=v(d);Te(m,1,_,Ve,(x,$)=>{var N=Se(()=>ea(n($),2));let b=()=>n(N)[0],h=()=>n(N)[1];var D=ze(),M=fe(D);Fs(M,b,!0,(k,Y)=>{_a(k,()=>({...h()}))}),T(x,D)});var p=i(m);nt(p,t,"default",{}),o(d),T(e,d),qe()}function cn(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];_t(e,pt({name:"download"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}function Ha(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];_t(e,pt({name:"file-text"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}function ja(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M9 18V5l12-2v13"}],["circle",{cx:"6",cy:"18",r:"3"}],["circle",{cx:"18",cy:"16",r:"3"}]];_t(e,pt({name:"music"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}function Va(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];_t(e,pt({name:"settings"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}function Ba(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M18 7V5a1 1 0 0 0-1-1H6.5a.5.5 0 0 0-.4.8l4.5 6a2 2 0 0 1 0 2.4l-4.5 6a.5.5 0 0 0 .4.8H17a1 1 0 0 0 1-1v-2"}]];_t(e,pt({name:"sigma"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}function Ga(e,t){const a=Xe(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const s=[["path",{d:"M21 5H3"}],["path",{d:"M15 12H3"}],["path",{d:"M17 19H3"}]];_t(e,pt({name:"text-align-start"},()=>a,{get iconNode(){return s},children:(l,c)=>{var r=ze(),u=fe(r);nt(u,t,"default",{}),T(l,r)},$$slots:{default:!0}}))}var vn=F('<button><!> <span class="label svelte-oeh3u8"> </span></button>'),un=F('<nav class="svelte-oeh3u8"></nav>');function dn(e){const t=()=>J(Ct,"$activeTab",a),[a,s]=Oe(),l=[{id:"parse",label:"Parse",icon:Ha},{id:"line",label:"Line",icon:Ga},{id:"meter",label:"Meter",icon:ja},{id:"maxent",label:"MaxEnt",icon:Ba},{id:"settings",label:"Settings",icon:Va}];var c=un();Te(c,5,()=>l,r=>r.id,(r,u)=>{var f=vn();let _;var d=v(f);n(u).icon(d,{size:20,strokeWidth:1.75});var m=i(d,2),p=v(m,!0);o(m),o(f),K(()=>{_=he(f,1,"svelte-oeh3u8",null,_,{active:t()===n(u).id}),I(p,n(u).label)}),U("click",f,()=>ce(Ct,n(u).id)),T(r,f)}),o(c),T(e,c),s()}We(["click"]);var fn=F('<div class="text-input svelte-d9edf1"><textarea placeholder="Paste poetry here..." class="svelte-d9edf1"></textarea></div>');function pn(e){const t=()=>J(At,"$inputText",a),[a,s]=Oe();var l=fn(),c=v(l);Es(c),o(l),ft(c,t,r=>ce(At,r)),T(e,l),s()}function ra(){return typeof window<"u"&&window.__PROSODIC_PORT__?`http://127.0.0.1:${window.__PROSODIC_PORT__}`:""}async function bt(e,t,a){const s={method:e,headers:a instanceof FormData?{}:{"Content-Type":"application/json"}};a&&(s.body=a instanceof FormData?a:JSON.stringify(a));const l=await fetch(`${ra()}${t}`,s);if(!l.ok){const c=await l.json().catch(()=>({detail:l.statusText}));throw new Error(c.detail||l.statusText)}return l.json()}function _n(){return bt("GET","/api/meter/defaults")}async function bn(e,{onProgress:t,onRows:a}){const s=await fetch(`${ra()}/api/parse/stream`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!s.ok){const f=await s.json().catch(()=>({detail:s.statusText}));throw new Error(f.detail||s.statusText)}const l=s.body.getReader(),c=new TextDecoder;let r="",u=null;for(;;){const{done:f,value:_}=await l.read();if(f)break;r+=c.decode(_,{stream:!0});const d=r.split(`
`);r=d.pop()||"";for(const m of d){if(!m.startsWith("data: "))continue;const p=JSON.parse(m.slice(6));p.phase==="progress"&&t?t(p.message):p.phase==="rows"&&a?a(p.rows):p.phase==="done"&&(u={elapsed:p.elapsed,num_lines:p.num_lines})}}return u}async function hn(e,t="csv"){const a=await fetch(`${ra()}/api/parse/export`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...e,format:t})});if(!a.ok){const r=await a.json().catch(()=>({detail:a.statusText}));throw new Error(r.detail||a.statusText)}const s=await a.blob(),l=URL.createObjectURL(s),c=document.createElement("a");c.href=l,c.download=`prosodic-parse.${t}`,document.body.appendChild(c),c.click(),c.remove(),URL.revokeObjectURL(l)}function gn(e){return bt("POST","/api/parse/line",e)}function mn(e){return bt("POST","/api/maxent/fit",e)}function xn(e,t){const a=new FormData;return a.append("annotations_file",e),t.constraints&&a.append("constraints",t.constraints.join(",")),a.append("max_s",t.max_s),a.append("max_w",t.max_w),a.append("resolve_optionality",t.resolve_optionality),a.append("zones",String(t.zones??"3")),a.append("regularization",t.regularization),a.append("syntax",t.syntax),bt("POST","/api/maxent/fit-annotations",a)}function wn(){return bt("GET","/api/corpora")}function $n(e){return bt("GET",`/api/corpora/read?path=${encodeURIComponent(e)}`)}var yn=F('<div class="export-menu svelte-e3u3bt" role="menu"><button class="svelte-e3u3bt">CSV</button> <button class="svelte-e3u3bt">TSV</button> <button class="svelte-e3u3bt">JSON</button></div>'),kn=F('<div class="pagination svelte-e3u3bt"><button class="pg-btn svelte-e3u3bt">&laquo;</button> <button class="pg-btn svelte-e3u3bt">&lsaquo;</button> <span class="pg-info svelte-e3u3bt"> <span class="pg-detail svelte-e3u3bt"> </span></span> <button class="pg-btn svelte-e3u3bt">&rsaquo;</button> <button class="pg-btn svelte-e3u3bt">&raquo;</button> <select class="pg-size svelte-e3u3bt"><option>50</option><option>100</option><option>250</option><option>500</option></select></div>'),Tn=F('<span class="parts-badge svelte-e3u3bt"> </span>'),zn=F('<tr><td class="svelte-e3u3bt"> <!></td><td class="parse-text svelte-e3u3bt"></td><td class="stat meter-cell svelte-e3u3bt"></td><td class="stat svelte-e3u3bt"> </td><td class="stat svelte-e3u3bt"> </td></tr>'),Cn=F('<div class="pagination bottom svelte-e3u3bt"><button class="pg-btn svelte-e3u3bt">&laquo;</button> <button class="pg-btn svelte-e3u3bt">&lsaquo;</button> <span class="pg-info svelte-e3u3bt"> </span> <button class="pg-btn svelte-e3u3bt">&rsaquo;</button> <button class="pg-btn svelte-e3u3bt">&raquo;</button></div>'),En=F('<div class="header-row svelte-e3u3bt"><span class="stat svelte-e3u3bt"> </span> <div class="toggle-row svelte-e3u3bt"><button>Best only</button> <button>All unbounded</button></div> <div class="export-wrap svelte-e3u3bt"><button class="export-btn svelte-e3u3bt" title="Export all unbounded parses"><!> </button> <!></div> <span class="legend svelte-e3u3bt"><span class="mtr_s">over</span>line = strong &nbsp; <span class="str_s svelte-e3u3bt">bold</span> = stressed &nbsp; <span class="viol_y svelte-e3u3bt">red</span> = violation</span></div> <!> <div class="table-wrap svelte-e3u3bt"><table class="svelte-e3u3bt"><thead><tr><th class="sortable svelte-e3u3bt"> </th><th class="svelte-e3u3bt">Parse</th><th class="sortable svelte-e3u3bt"> </th><th class="sortable svelte-e3u3bt"> </th><th class="sortable svelte-e3u3bt"> </th></tr></thead><tbody></tbody></table></div> <!>',1);function Sn(e,t){Ne(t,!0);const a=()=>J(ut,"$zoneWeights",f),s=()=>J(Ee,"$meterConfig",f),l=()=>J(Ze,"$constraintWeights",f),c=()=>J(At,"$inputText",f),r=()=>J(De,"$settings",f),u=()=>J(Je,"$maxentConfig",f),[f,_]=Oe();let d=Ce(t,"rows",19,()=>[]),m=Ce(t,"elapsed",3,0),p=Ce(t,"numLines",3,0),x=Ce(t,"onLineClick",3,null),$=ae("best"),N=ae(null),b=ae(!0),h=ae(1),D=ae(100),M=ae(!1),k=ae(!1);function Y(){const w=a()?s().constraints:s().constraints.map(O=>{const g=l()[O];return g!=null&&g!==1?`${O}/${g}`:O}),y={text:c(),constraints:w,max_s:s().max_s,max_w:s().max_w,resolve_optionality:s().resolve_optionality,syntax:r().syntax,syntax_model:r().syntax_model};return a()&&(y.zone_weights=a(),y.zones=u().zones),y}async function C(w){S(k,!1),S(M,!0);try{await hn(Y(),w)}catch(y){alert(`Export failed: ${y.message}`)}finally{S(M,!1)}}function E(w){n(N)===w?S(b,!n(b)):(S(N,w,!0),S(b,!0)),S(h,1)}let R=Se(()=>{let w=n($)==="best"?d().filter(y=>y.rank===1):d();return n(N)&&(w=[...w].sort((y,O)=>{let g=y[n(N)],W=O[n(N)];return typeof g=="string"?n(b)?g.localeCompare(W):W.localeCompare(g):n(b)?g-W:W-g})),w}),z=Se(()=>Math.max(1,Math.ceil(n(R).length/n(D)))),q=Se(()=>n(R).slice((n(h)-1)*n(D),n(h)*n(D)));ta(()=>{d(),S(h,1)});function j(w){return n(N)!==w?"":n(b)?" ▲":" ▼"}function L(w){S(h,Math.max(1,Math.min(w,n(z))),!0)}var X=ze(),P=fe(X);{var B=w=>{var y=En(),O=fe(y),g=v(O),W=v(g);o(g);var H=i(g,2),G=v(H);let te;var ve=i(G,2);let ne;o(H);var le=i(H,2),ie=v(le),oe=v(ie);cn(oe,{size:14,strokeWidth:1.75});var pe=i(oe);o(ie);var ge=i(ie,2);{var me=re=>{var Z=yn(),de=v(Z),_e=i(de,2),be=i(_e,2);o(Z),U("click",de,()=>C("csv")),U("click",_e,()=>C("tsv")),U("click",be,()=>C("json")),T(re,Z)};se(ge,re=>{n(k)&&re(me)})}o(le),Ss(2),o(O);var Le=i(O,2);{var Me=re=>{var Z=kn(),de=v(Z),_e=i(de,2),be=i(_e,2),Fe=v(be),Ge=i(Fe),rt=v(Ge);o(Ge),o(be);var et=i(be,2),tt=i(et,2),Ue=i(tt,2),mt=v(Ue);mt.value=mt.__value=50;var lt=i(mt);lt.value=lt.__value=100;var xt=i(lt);xt.value=xt.__value=250;var it=i(xt);it.value=it.__value=500,o(Ue),o(Z),K(()=>{de.disabled=n(h)<=1,_e.disabled=n(h)<=1,I(Fe,`Page ${n(h)??""} of ${n(z)??""} `),I(rt,`(${n(R).length??""} rows, ${n(D)??""}/page)`),et.disabled=n(h)>=n(z),tt.disabled=n(h)>=n(z)}),U("click",de,()=>L(1)),U("click",_e,()=>L(n(h)-1)),U("click",et,()=>L(n(h)+1)),U("click",tt,()=>L(n(z))),U("change",Ue,()=>S(h,1)),dt(Ue,()=>n(D),ot=>S(D,ot)),T(re,Z)};se(Le,re=>{n(z)>1&&re(Me)})}var xe=i(Le,2),ye=v(xe),Be=v(ye),Qe=v(Be),Re=v(Qe),ht=v(Re);o(Re);var we=i(Re,2),A=v(we);o(we);var V=i(we),ue=v(V);o(V);var $e=i(V),Ie=v($e);o($e),o(Qe),o(Be);var Pt=i(Be);Te(Pt,21,()=>n(q),re=>re.line_num+"-"+re.rank,(re,Z)=>{var de=zn();let _e;var be=v(de),Fe=v(be),Ge=i(Fe);{var rt=it=>{var ot=Tn(),Ya=v(ot);o(ot),K(()=>{Lt(ot,"title",`Line parsed as ${n(Z).num_parts??""} lineparts`),I(Ya,`·${n(Z).num_parts??""}`)}),T(it,ot)};se(Ge,it=>{n(Z).num_parts&&n(Z).num_parts>1&&it(rt)})}o(be);var et=i(be);Kt(et,()=>n(Z).parse_html,!0),o(et);var tt=i(et);Kt(tt,()=>n(Z).meter_str,!0),o(tt);var Ue=i(tt),mt=v(Ue,!0);o(Ue);var lt=i(Ue),xt=v(lt,!0);o(lt),o(de),K(()=>{_e=he(de,1,"svelte-e3u3bt",null,_e,{best:n(Z).rank===1,other:n(Z).rank!==1,clickable:n(Z).rank===1&&x()}),I(Fe,`${n(Z).line_num??""} `),I(mt,n(Z).score),I(xt,n(Z).rank===1?n(Z).num_unbounded:"")}),U("click",de,()=>n(Z).rank===1&&x()&&x()(n(Z))),T(re,de)}),o(Pt),o(ye),o(xe);var Dt=i(xe,2);{var gt=re=>{var Z=Cn(),de=v(Z),_e=i(de,2),be=i(_e,2),Fe=v(be);o(be);var Ge=i(be,2),rt=i(Ge,2);o(Z),K(()=>{de.disabled=n(h)<=1,_e.disabled=n(h)<=1,I(Fe,`Page ${n(h)??""} of ${n(z)??""}`),Ge.disabled=n(h)>=n(z),rt.disabled=n(h)>=n(z)}),U("click",de,()=>L(1)),U("click",_e,()=>L(n(h)-1)),U("click",Ge,()=>L(n(h)+1)),U("click",rt,()=>L(n(z))),T(re,Z)};se(Dt,re=>{n(z)>1&&re(gt)})}K((re,Z,de,_e,be,Fe)=>{I(W,`Parsed ${p()??""} lines in ${re??""}s (${Z??""} best, ${d().length??""} total)`),te=he(G,1,"toggle-btn svelte-e3u3bt",null,te,{active:n($)==="best"}),ne=he(ve,1,"toggle-btn svelte-e3u3bt",null,ne,{active:n($)==="unbounded"}),ie.disabled=n(M),I(pe,` ${n(M)?"Exporting…":"Export"}`),I(ht,`Line${de??""}`),I(A,`Meter${_e??""}`),I(ue,`Score${be??""}`),I(Ie,`Ambig${Fe??""}`)},[()=>m().toFixed(2),()=>d().filter(re=>re.rank===1).length,()=>j("line_num"),()=>j("meter_str"),()=>j("score"),()=>j("num_unbounded")]),U("click",G,()=>{S($,"best"),S(h,1)}),U("click",ve,()=>{S($,"unbounded"),S(h,1)}),U("click",ie,()=>S(k,!n(k))),U("click",Re,()=>E("line_num")),U("click",we,()=>E("meter_str")),U("click",V,()=>E("score")),U("click",$e,()=>E("num_unbounded")),T(w,y)};se(P,w=>{d().length>0&&w(B)})}T(e,X),qe(),_()}We(["click","change"]);var An=F("<option> </option>"),Ln=F('<select class="corpus-select svelte-h69i1w"><option> </option><!></select>');function Ua(e,t){Ne(t,!0);const a=()=>J(ua,"$corporaList",s),[s,l]=Oe();let c=Ce(t,"onLoad",3,null),r=ae(!1);Ma(async()=>{if(a().length===0)try{const m=await wn();ce(ua,m.files)}catch(m){console.error("Failed to load corpora:",m)}});async function u(m){const p=m.target.value;if(p){S(r,!0);try{const x=await $n(p);c()?c()(x.text,x.name):ce(At,x.text)}catch(x){console.error("Failed to read corpus:",x)}finally{S(r,!1),m.target.value=""}}}var f=ze(),_=fe(f);{var d=m=>{var p=Ln(),x=v(p),$=v(x,!0);o(x),x.value=x.__value="";var N=i(x);Te(N,1,a,Ve,(b,h)=>{var D=An(),M=v(D);o(D);var k={};K(()=>{I(M,`${n(h).name??""} (${n(h).num_lines??""} lines)`),k!==(k=n(h).path)&&(D.value=(D.__value=n(h).path)??"")}),T(b,D)}),o(p),K(()=>{p.disabled=n(r),I($,n(r)?"Loading...":"Load from corpus...")}),U("change",p,u),T(m,p)};se(_,m=>{a().length>0&&m(d)})}T(e,f),qe(),l()}We(["change"]);var Mn=F('<span class="spinner svelte-1uxxkri"></span> ',1),Pn=F('<div class="error svelte-1uxxkri"> </div>'),Nn=F('<div class="empty svelte-1uxxkri">Paste text and hit Parse</div>'),qn=F('<div class="page svelte-1uxxkri"><aside class="input-col svelte-1uxxkri"><div class="input-sticky svelte-1uxxkri"><!> <!> <button class="action-btn svelte-1uxxkri"><!></button> <button class="meter-link svelte-1uxxkri">Meter settings</button></div></aside> <section class="results-col svelte-1uxxkri"><!> <!></section></div>');function On(e,t){Ne(t,!0);const a=()=>J(ut,"$zoneWeights",_),s=()=>J(Ee,"$meterConfig",_),l=()=>J(Ze,"$constraintWeights",_),c=()=>J(jt,"$parseLoading",_),r=()=>J(At,"$inputText",_),u=()=>J(De,"$settings",_),f=()=>J(Je,"$maxentConfig",_),[_,d]=Oe();let m=ae(""),p=ae(""),x=ae(aa([])),$=ae(0),N=ae(0);function b(){return a()?s().constraints:s().constraints.map(g=>{const W=l()[g];return W!=null&&W!==1?`${g}/${W}`:g})}async function h(){S(m,""),S(x,[],!0),S($,0),S(N,0),ce(jt,!0),S(p,"Starting...");try{const g={text:r(),constraints:b(),max_s:s().max_s,max_w:s().max_w,resolve_optionality:s().resolve_optionality,syntax:u().syntax,syntax_model:u().syntax_model};a()&&(g.zone_weights=a(),g.zones=f().zones);const W=await bn(g,{onProgress:H=>{S(p,H,!0)},onRows:H=>{S(x,[...n(x),...H],!0)}});W&&(S($,W.elapsed,!0),S(N,W.num_lines,!0))}catch(g){S(m,g.message,!0)}finally{ce(jt,!1),S(p,"")}}function D(g){ce(Ot,{line_num:g.line_num,line_text:g.line_text}),Rt("line")}var M=qn(),k=v(M),Y=v(k),C=v(Y);Ua(C,{});var E=i(C,2);pn(E);var R=i(E,2),z=v(R);{var q=g=>{var W=Mn(),H=i(fe(W));K(()=>I(H,` ${(n(p)||"Parsing...")??""}`)),T(g,W)},j=g=>{var W=Yt("Parse");T(g,W)};se(z,g=>{c()?g(q):g(j,-1)})}o(R);var L=i(R,2);o(Y),o(k);var X=i(k,2),P=v(X);{var B=g=>{var W=Pn(),H=v(W,!0);o(W),K(()=>I(H,n(m))),T(g,W)};se(P,g=>{n(m)&&g(B)})}var w=i(P,2);{var y=g=>{Sn(g,{get rows(){return n(x)},get elapsed(){return n($)},get numLines(){return n(N)},onLineClick:D})},O=g=>{var W=Nn();T(g,W)};se(w,g=>{n(x).length>0?g(y):c()||g(O,1)})}o(X),o(M),K(()=>R.disabled=c()),U("click",R,h),U("click",L,()=>Rt("meter")),T(e,M),qe(),d()}We(["click"]);var Wn=F('<p class="override-note svelte-putzd4">Manual weights are overridden by MaxEnt zone weights below. Reset weights to use manual values.</p>'),Rn=F('<span class="c-desc svelte-putzd4"> </span>'),In=F('<div><div class="c-info svelte-putzd4"><span class="c-name svelte-putzd4"> </span> <!></div> <input class="c-weight svelte-putzd4" type="number" step="0.1" min="0"/> <input class="c-check svelte-putzd4" type="checkbox"/></div>'),Fn=F('<div class="zone-row svelte-putzd4"><span class="z-name svelte-putzd4"> </span> <span class="z-weight svelte-putzd4"> </span> <div class="z-bar svelte-putzd4"></div></div>'),Dn=F('<section class="section svelte-putzd4"><h3 class="section-title svelte-putzd4">Zone Weights <span class="badge svelte-putzd4">from MaxEnt</span></h3> <p class="zone-note svelte-putzd4">These zone-expanded weights were learned by MaxEnt training and are used for scoring. Reset to clear.</p> <div class="zone-list"></div></section>'),Hn=F("<option> </option>"),jn=F("<option> </option>"),Vn=F('<div class="page svelte-putzd4"><h2 class="page-title svelte-putzd4">Meter Configuration</h2> <p class="page-desc svelte-putzd4">Configure constraints and weights used by the parser. MaxEnt training will update weights automatically.</p> <div class="actions svelte-putzd4"><button class="btn svelte-putzd4">Reset Constraints</button> <button class="btn svelte-putzd4">Reset Weights</button></div> <section class="section svelte-putzd4"><h3 class="section-title svelte-putzd4">Constraints</h3> <!> <div class="constraint-header svelte-putzd4"><span class="ch-name svelte-putzd4">Constraint</span> <span class="ch-weight svelte-putzd4">Weight</span> <span class="ch-on svelte-putzd4">On</span></div> <!></section> <!> <section class="section svelte-putzd4"><h3 class="section-title svelte-putzd4">Position Sizes</h3> <label class="config-row svelte-putzd4"><span>max_w <span class="c-desc svelte-putzd4">Max syllables in weak position</span></span> <select class="svelte-putzd4"></select></label> <label class="config-row svelte-putzd4"><span>max_s <span class="c-desc svelte-putzd4">Max syllables in strong position</span></span> <select class="svelte-putzd4"></select></label> <label class="config-row svelte-putzd4"><span>resolve_optionality</span> <input type="checkbox"/></label></section></div>');function Bn(e,t){Ne(t,!0);const a=()=>J(Na,"$defaultConstraints",f),s=()=>J(ut,"$zoneWeights",f),l=()=>J(Oa,"$allConstraints",f),c=()=>J(Ee,"$meterConfig",f),r=()=>J(qa,"$constraintDescriptions",f),u=()=>J(Ze,"$constraintWeights",f),[f,_]=Oe();function d(w){Ee.update(y=>(y.constraints.indexOf(w)>=0?y.constraints=y.constraints.filter(g=>g!==w):y.constraints=[...y.constraints,w],y))}function m(w,y){Ze.update(O=>({...O,[w]:parseFloat(y)||0}))}function p(){Ee.update(w=>({...w,constraints:[...a()],max_s:2,max_w:2,resolve_optionality:!0}))}function x(){Ze.update(w=>{const y={};for(const O of Object.keys(w))y[O]=1;return y}),ce(ut,null)}let $=Se(()=>s()!=null);var N=Vn(),b=i(v(N),4),h=v(b),D=i(h,2);o(b);var M=i(b,2),k=i(v(M),2);{var Y=w=>{var y=Wn();T(w,y)};se(k,w=>{n($)&&w(Y)})}var C=i(k,4);Te(C,1,l,Ve,(w,y)=>{const O=Se(()=>c().constraints.includes(n(y)));var g=In();let W;var H=v(g),G=v(H),te=v(G);o(G);var ve=i(G,2);{var ne=oe=>{var pe=Rn(),ge=v(pe,!0);o(pe),K(()=>I(ge,r()[n(y)])),T(oe,pe)};se(ve,oe=>{r()[n(y)]&&oe(ne)})}o(H);var le=i(H,2);Ae(le);var ie=i(le,2);Ae(ie),o(g),K(()=>{W=he(g,1,"constraint-row svelte-putzd4",null,W,{inactive:!n(O),overridden:n($)}),I(te,`*${n(y)??""}`),Zs(le,u()[n(y)]??1),le.disabled=!n(O)||n($),Xs(ie,n(O))}),U("input",le,oe=>m(n(y),oe.target.value)),U("change",ie,()=>d(n(y))),T(w,g)}),o(M);var E=i(M,2);{var R=w=>{var y=Dn(),O=i(v(y),4);Te(O,5,()=>Object.entries(s()).sort((g,W)=>W[1]-g[1]),Ve,(g,W)=>{var H=Se(()=>ea(n(W),2));let G=()=>n(H)[0],te=()=>n(H)[1];var ve=ze(),ne=fe(ve);{var le=ie=>{var oe=Fn(),pe=v(oe),ge=v(pe,!0);o(pe);var me=i(pe,2),Le=v(me,!0);o(me);var Me=i(me,2);o(oe),K((xe,ye)=>{I(ge,G()),I(Le,xe),sa(Me,`width: ${ye??""}%`)},[()=>te().toFixed(3),()=>Math.min(te()/Object.values(s()).reduce((xe,ye)=>Math.max(xe,ye),1)*100,100).toFixed(0)]),T(ie,oe)};se(ne,ie=>{te()>.001&&ie(le)})}T(g,ve)}),o(O),o(y),T(w,y)};se(E,w=>{n($)&&w(R)})}var z=i(E,2),q=i(v(z),2),j=i(v(q),2);Te(j,20,()=>[1,2,3,4,5],Ve,(w,y)=>{var O=Hn(),g=v(O,!0);o(O);var W={};K(()=>{I(g,y),W!==(W=y)&&(O.value=(O.__value=y)??"")}),T(w,O)}),o(j),o(q);var L=i(q,2),X=i(v(L),2);Te(X,20,()=>[1,2,3,4,5],Ve,(w,y)=>{var O=jn(),g=v(O,!0);o(O);var W={};K(()=>{I(g,y),W!==(W=y)&&(O.value=(O.__value=y)??"")}),T(w,O)}),o(X),o(L);var P=i(L,2),B=i(v(P),2);Ae(B),o(P),o(z),o(N),U("click",h,p),U("click",D,x),dt(j,()=>c().max_w,w=>ke(Ee,ee(c).max_w=w,ee(c))),dt(X,()=>c().max_s,w=>ke(Ee,ee(c).max_s=w,ee(c))),na(B,()=>c().resolve_optionality,w=>ke(Ee,ee(c).resolve_optionality=w,ee(c))),T(e,N),qe(),_()}We(["click","input","change"]);var Gn=F('<div class="stat-row accent svelte-170wde3"><span class="stat-label svelte-170wde3">Accuracy</span> <span class="stat-value svelte-170wde3"> <span class="detail svelte-170wde3"> </span></span></div>'),Un=F('<div class="stat-row svelte-170wde3"><span class="stat-label svelte-170wde3">Log-likelihood</span> <span class="stat-value svelte-170wde3"> </span></div>'),Yn=F('<tr><td class="svelte-170wde3"> </td><td class="mono svelte-170wde3"> </td><td class="bar-cell svelte-170wde3"><div class="bar svelte-170wde3"></div></td></tr>'),Jn=F('<h3 class="weights-title svelte-170wde3">Learned Weights</h3> <table class="svelte-170wde3"><thead><tr><th class="svelte-170wde3">Constraint</th><th class="svelte-170wde3">Weight</th><th class="svelte-170wde3"></th></tr></thead><tbody></tbody></table>',1),Kn=F('<div class="empty svelte-170wde3">No weights learned (all zero)</div>'),Zn=F('<div class="stats svelte-170wde3"><div class="stat-row svelte-170wde3"><span class="stat-label svelte-170wde3">Trained on</span> <span class="stat-value svelte-170wde3"> </span></div> <!> <!> <div class="stat-row svelte-170wde3"><span class="stat-label svelte-170wde3">Config</span> <span class="stat-value detail svelte-170wde3"> </span></div> <div class="stat-row svelte-170wde3"><span class="stat-label svelte-170wde3">Time</span> <span class="stat-value svelte-170wde3"> </span></div></div> <!>',1);function Xn(e,t){Ne(t,!0);function a(r){return!r||r.length===0?1:r[0].weight}var s=ze(),l=fe(s);{var c=r=>{var u=Zn(),f=fe(u),_=v(f),d=i(v(_),2),m=v(d);o(d),o(_);var p=i(_,2);{var x=z=>{var q=Gn(),j=i(v(q),2),L=v(j),X=i(L),P=v(X);o(X),o(j),o(q),K(B=>{I(L,`${B??""}% `),I(P,`(${t.result.num_matched??""}/${t.result.num_lines??""} correct)`)},[()=>(t.result.accuracy*100).toFixed(1)]),T(z,q)};se(p,z=>{t.result.accuracy!=null&&z(x)})}var $=i(p,2);{var N=z=>{var q=Un(),j=i(v(q),2),L=v(j,!0);o(j),o(q),K(X=>I(L,X),[()=>t.result.log_likelihood.toFixed(2)]),T(z,q)};se($,z=>{t.result.log_likelihood!=null&&z(N)})}var b=i($,2),h=i(v(b),2),D=v(h);o(h),o(b);var M=i(b,2),k=i(v(M),2),Y=v(k);o(k),o(M),o(f);var C=i(f,2);{var E=z=>{var q=Jn(),j=i(fe(q),2),L=i(v(j));Te(L,21,()=>t.result.weights,Ve,(X,P)=>{var B=Yn(),w=v(B),y=v(w,!0);o(w);var O=i(w),g=v(O,!0);o(O);var W=i(O),H=v(W);o(W),o(B),K((G,te)=>{I(y,n(P).name),I(g,G),sa(H,`width: ${te??""}%`)},[()=>n(P).weight.toFixed(3),()=>(n(P).weight/a(t.result.weights)*100).toFixed(0)]),T(X,B)}),o(L),o(j),T(z,q)},R=z=>{var q=Kn();T(z,q)};se(C,z=>{t.result.weights.length>0?z(E):z(R,-1)})}K(z=>{I(m,`${t.result.num_lines??""} lines`),I(D,`${t.result.config.target!=="(from annotations)"?`target: ${t.result.config.target}`:"from annotations"},
				zones: ${t.result.config.zones??""},
				reg: ${t.result.config.regularization??""}`),I(Y,`${z??""}s`)},[()=>t.result.elapsed.toFixed(2)]),T(r,u)};se(l,r=>{t.result&&r(c)})}T(e,s),qe()}var Qn=F('<div class="corpus-badge svelte-584km6"> </div>'),er=F('<span class="spinner svelte-584km6"></span> ',1),tr=F('<span class="spinner svelte-584km6"></span> ',1),ar=F('<div class="error svelte-584km6"> </div>'),sr=F('<div class="page svelte-584km6"><h2 class="page-title svelte-584km6">MaxEnt Weight Learning</h2> <p class="page-desc svelte-584km6">Train constraint weights from a text corpus or annotated scansion data. Learned weights are saved to Meter config.</p> <section class="section svelte-584km6"><h3 class="section-title svelte-584km6">Train from Text + Target Scansion</h3> <!> <!> <div class="field svelte-584km6"><label class="svelte-584km6">Or upload a file <span class="desc svelte-584km6">Plain text, one line of verse per line</span></label> <input type="file" accept=".txt" class="svelte-584km6"/></div> <div class="field svelte-584km6"><label class="svelte-584km6">Target scansion <span class="desc svelte-584km6">e.g. wswswswsws for iambic pentameter</span></label> <input type="text" class="text-input svelte-584km6"/></div> <button class="action-btn svelte-584km6"><!></button></section> <section class="section svelte-584km6"><h3 class="section-title svelte-584km6">Train from Annotations</h3> <div class="field svelte-584km6"><label class="svelte-584km6">Annotations file <span class="desc svelte-584km6">TSV with columns: text, scansion, frequency</span></label> <input type="file" accept=".tsv,.csv,.txt" class="svelte-584km6"/></div> <button class="action-btn secondary svelte-584km6"><!></button></section> <section class="section svelte-584km6"><h3 class="section-title svelte-584km6">Training Parameters</h3> <label class="config-row svelte-584km6"><span>Zones <span class="desc svelte-584km6">Positional zone splitting</span></span> <select class="svelte-584km6"><option>None</option><option>2</option><option>3</option><option>Initial</option><option>Foot</option></select></label> <label class="config-row svelte-584km6"><span>Regularization <span class="desc svelte-584km6">L2 penalty (higher = more conservative)</span></span> <input type="number" class="num-input svelte-584km6" step="10" min="1"/></label> <label class="config-row svelte-584km6"><span>Syntax <span class="desc svelte-584km6">Add phrasal stress via spaCy</span></span> <input type="checkbox"/></label></section> <!> <!></div>');function nr(e,t){Ne(t,!0);const a=()=>J(Ee,"$meterConfig",u),s=()=>J(Ze,"$constraintWeights",u),l=()=>J(wt,"$maxentLoading",u),c=()=>J($t,"$maxentWeights",u),r=()=>J(Je,"$maxentConfig",u),[u,f]=Oe();let _=ae(""),d=ae(""),m=ae(null),p=ae(null),x=ae(""),$=ae("");function N(A,V){S(x,A,!0),S($,V,!0),n(p)&&(n(p).value="")}function b(){return a().constraints.map(A=>{const V=s()[A];return V!=null&&V!==1?`${A}/${V}`:A})}function h(A){if(!A||!A.weights)return;const V={};for(const ue of A.weights)V[ue.name]=ue.weight;ce(ut,V)}async function D(){var ue,$e;const A=($e=(ue=n(p))==null?void 0:ue.files)==null?void 0:$e[0];let V=n(x);if(A&&(V=await A.text()),!V){S(_,"Select a corpus or upload a text file");return}S(_,""),ce(wt,!0),ce($t,null),S(d,"Training weights...");try{const Ie=await mn({text:V,constraints:b(),max_s:a().max_s,max_w:a().max_w,resolve_optionality:a().resolve_optionality,target_scansion:r().target_scansion,zones:r().zones,regularization:r().regularization,syntax:r().syntax});ce($t,Ie),h(Ie)}catch(Ie){S(_,Ie.message,!0)}finally{ce(wt,!1),S(d,"")}}async function M(){var V,ue;const A=(ue=(V=n(m))==null?void 0:V.files)==null?void 0:ue[0];if(!A){S(_,"Please select an annotations file");return}S(_,""),ce(wt,!0),ce($t,null),S(d,"Training from annotations...");try{const $e=await xn(A,{constraints:b(),max_s:a().max_s,max_w:a().max_w,resolve_optionality:a().resolve_optionality,zones:r().zones,regularization:r().regularization,syntax:r().syntax});ce($t,$e),h($e)}catch($e){S(_,$e.message,!0)}finally{ce(wt,!1),S(d,"")}}var k=sr(),Y=i(v(k),4),C=i(v(Y),2);Ua(C,{onLoad:N});var E=i(C,2);{var R=A=>{var V=Qn(),ue=v(V);o(V),K(()=>I(ue,`Using: ${n($)??""}`)),T(A,V)};se(E,A=>{n($)&&A(R)})}var z=i(E,2),q=i(v(z),2);ca(q,A=>S(p,A),()=>n(p)),o(z);var j=i(z,2),L=i(v(j),2);Ae(L),o(j);var X=i(j,2),P=v(X);{var B=A=>{var V=er(),ue=i(fe(V));K(()=>I(ue,` ${n(d)??""}`)),T(A,V)},w=Se(()=>l()&&n(d).includes("Training w")),y=A=>{var V=Yt("Train from Text");T(A,V)};se(P,A=>{n(w)?A(B):A(y,-1)})}o(X),o(Y);var O=i(Y,2),g=i(v(O),2),W=i(v(g),2);ca(W,A=>S(m,A),()=>n(m)),o(g);var H=i(g,2),G=v(H);{var te=A=>{var V=tr(),ue=i(fe(V));K(()=>I(ue,` ${n(d)??""}`)),T(A,V)},ve=Se(()=>l()&&n(d).includes("annotation")),ne=A=>{var V=Yt("Train from Annotations");T(A,V)};se(G,A=>{n(ve)?A(te):A(ne,-1)})}o(H),o(O);var le=i(O,2),ie=i(v(le),2),oe=i(v(ie),2),pe=v(oe);pe.value=(pe.__value=null)??"";var ge=i(pe);ge.value=ge.__value=2;var me=i(ge);me.value=me.__value=3;var Le=i(me);Le.value=Le.__value="initial";var Me=i(Le);Me.value=Me.__value="foot",o(oe),o(ie);var xe=i(ie,2),ye=i(v(xe),2);Ae(ye),o(xe);var Be=i(xe,2),Qe=i(v(Be),2);Ae(Qe),o(Be),o(le);var Re=i(le,2);{var ht=A=>{var V=ar(),ue=v(V,!0);o(V),K(()=>I(ue,n(_))),T(A,V)};se(Re,A=>{n(_)&&A(ht)})}var we=i(Re,2);Xn(we,{get result(){return c()}}),o(k),K(()=>{X.disabled=l(),H.disabled=l()}),U("change",q,()=>{S(x,""),S($,"")}),ft(L,()=>r().target_scansion,A=>ke(Je,ee(r).target_scansion=A,ee(r))),U("click",X,D),U("click",H,M),dt(oe,()=>r().zones,A=>ke(Je,ee(r).zones=A,ee(r))),ft(ye,()=>r().regularization,A=>ke(Je,ee(r).regularization=A,ee(r))),na(Qe,()=>r().syntax,A=>ke(Je,ee(r).syntax=A,ee(r))),T(e,k),qe(),f()}We(["change","click"]);var rr=F('<div class="error svelte-1povw2e"> </div>'),lr=F('<span class="viol-badge svelte-1povw2e"> <span class="viol-count svelte-1povw2e"> </span></span>'),ir=F('<span class="no-viols svelte-1povw2e">none</span>'),or=F('<tr><td class="rank-col svelte-1povw2e"> </td><td class="parse-text svelte-1povw2e"></td><td class="meter-col mono svelte-1povw2e"> </td><td class="score-col mono svelte-1povw2e"> </td><td class="viol-col svelte-1povw2e"><!></td></tr>'),cr=F('<div class="line-header svelte-1povw2e"><span class="line-text svelte-1povw2e"> </span> <span class="meta svelte-1povw2e"> </span></div> <div class="table-wrap svelte-1povw2e"><table class="svelte-1povw2e"><thead><tr><th class="rank-col svelte-1povw2e">#</th><th class="svelte-1povw2e">Scansion</th><th class="meter-col svelte-1povw2e">Meter</th><th class="score-col svelte-1povw2e">Score</th><th class="svelte-1povw2e">Violations</th></tr></thead><tbody></tbody></table></div>',1),vr=F('<div class="empty svelte-1povw2e">Press Enter or click Parse to analyze</div>'),ur=F('<div class="empty svelte-1povw2e">Click a line in Parse results or type a line above</div>'),dr=F('<div class="page svelte-1povw2e"><h2 class="page-title svelte-1povw2e">Line View</h2> <p class="page-desc svelte-1povw2e">Detailed analysis of a single line. Click a line in Parse results or type one below.</p> <div class="input-row svelte-1povw2e"><input type="text" class="line-input svelte-1povw2e" placeholder="Enter a line of verse..."/> <button class="parse-btn svelte-1povw2e"> </button></div> <!> <!></div>');function fr(e,t){Ne(t,!0);const a=()=>J(Ot,"$selectedLine",u),s=()=>J(ut,"$zoneWeights",u),l=()=>J(Ee,"$meterConfig",u),c=()=>J(Ze,"$constraintWeights",u),r=()=>J(Je,"$maxentConfig",u),[u,f]=Oe();let _=ae(""),d=ae(aa([])),m=ae(""),p=ae(!1),x=ae(""),$=ae(0),N=ae(0);ta(()=>{const P=a();P&&P.line_text&&(S(_,P.line_text,!0),h(P.line_text))});function b(){return s()?l().constraints:l().constraints.map(P=>{const B=c()[P];return B!=null&&B!==1?`${P}/${B}`:P})}async function h(P){const B=(P||n(_)).trim();if(B){S(p,!0),S(x,""),S(d,[],!0);try{const w={text:B,constraints:b(),max_s:l().max_s,max_w:l().max_w,resolve_optionality:l().resolve_optionality};s()&&(w.zone_weights=s(),w.zones=r().zones);const y=await gn(w);S(d,y.parses||[],!0),S(m,y.line_text||B,!0),S($,y.elapsed||0,!0),S(N,y.num_unbounded||0,!0)}catch(w){S(x,w.message,!0)}finally{S(p,!1)}}}function D(P){P.key==="Enter"&&(ce(Ot,null),h())}var M=dr(),k=i(v(M),4),Y=v(k);Ae(Y);var C=i(Y,2),E=v(C,!0);o(C),o(k);var R=i(k,2);{var z=P=>{var B=rr(),w=v(B,!0);o(B),K(()=>I(w,n(x))),T(P,B)};se(R,P=>{n(x)&&P(z)})}var q=i(R,2);{var j=P=>{var B=cr(),w=fe(B),y=v(w),O=v(y,!0);o(y);var g=i(y,2),W=v(g);o(g),o(w);var H=i(w,2),G=v(H),te=i(v(G));Te(te,21,()=>n(d),Ve,(ve,ne)=>{var le=or();let ie;var oe=v(le),pe=v(oe,!0);o(oe);var ge=i(oe);Kt(ge,()=>n(ne).parse_html,!0),o(ge);var me=i(ge),Le=v(me,!0);o(me);var Me=i(me),xe=v(Me,!0);o(Me);var ye=i(Me),Be=v(ye);{var Qe=we=>{var A=ze(),V=fe(A);Te(V,17,()=>Object.entries(n(ne).viol_summary),Ve,(ue,$e)=>{var Ie=Se(()=>ea(n($e),2));let Pt=()=>n(Ie)[0],Dt=()=>n(Ie)[1];var gt=lr(),re=v(gt),Z=i(re),de=v(Z,!0);o(Z),o(gt),K(()=>{I(re,`*${Pt()??""}`),I(de,Dt())}),T(ue,gt)}),T(we,A)},Re=Se(()=>Object.keys(n(ne).viol_summary).length>0),ht=we=>{var A=ir();T(we,A)};se(Be,we=>{n(Re)?we(Qe):we(ht,-1)})}o(ye),o(le),K(()=>{ie=he(le,1,"svelte-1povw2e",null,ie,{best:n(ne).rank===1,bounded:n(ne).is_bounded}),I(pe,n(ne).rank),I(Le,n(ne).meter_str),I(xe,n(ne).score)}),T(ve,le)}),o(te),o(G),o(H),K(ve=>{I(O,n(m)),I(W,`${n(N)??""} unbounded, ${n(d).length-n(N)} bounded (${n(d).length??""} total) in ${ve??""}s`)},[()=>n($).toFixed(2)]),T(P,B)},L=P=>{var B=vr();T(P,B)},X=P=>{var B=ur();T(P,B)};se(q,P=>{n(d).length>0?P(j):!n(p)&&n(_)?P(L,1):n(p)||P(X,2)})}o(M),K(()=>{C.disabled=n(p),I(E,n(p)?"Parsing...":"Parse")}),U("keydown",Y,D),ft(Y,()=>n(_),P=>S(_,P)),U("click",C,()=>{ce(Ot,null),h()}),T(e,M),qe(),f()}We(["keydown","click"]);var pr=F('<div class="page svelte-6bql28"><h2 class="page-title svelte-6bql28">Settings</h2> <p class="page-desc svelte-6bql28">Global options for parsing and analysis.</p> <section class="section svelte-6bql28"><h3 class="section-title svelte-6bql28">Syntax</h3> <label class="config-row svelte-6bql28"><div class="svelte-6bql28"><span>Enable phrasal stress</span> <span class="desc svelte-6bql28">Compute phrasal prominence via spaCy dependency parsing (Liberman & Prince 1977). Enables w_prom and s_demoted constraints.</span></div> <input type="checkbox"/></label> <label class="config-row svelte-6bql28"><div class="svelte-6bql28"><span>spaCy model</span> <span class="desc svelte-6bql28">Dependency parse model for phrasal stress</span></div> <select class="svelte-6bql28"><option>en_core_web_sm</option><option>en_core_web_md</option><option>en_core_web_lg</option><option>en_core_web_trf</option></select></label></section> <section class="section svelte-6bql28"><h3 class="section-title svelte-6bql28">Language</h3> <label class="config-row svelte-6bql28"><div class="svelte-6bql28"><span>Default language</span> <span class="desc svelte-6bql28">Language for tokenization and pronunciation lookup</span></div> <select class="svelte-6bql28"><option>English</option><option>Finnish</option></select></label></section> <section class="section svelte-6bql28"><h3 class="section-title svelte-6bql28">Performance</h3> <label class="config-row svelte-6bql28"><div class="svelte-6bql28"><span>Max syllables per parse unit</span> <span class="desc svelte-6bql28">Lines longer than this are skipped (exponential complexity). Default 14.</span></div> <input type="number" class="num-input svelte-6bql28" min="6" max="30" step="1"/></label> <label class="config-row svelte-6bql28"><div class="svelte-6bql28"><span>Parse timeout (seconds)</span> <span class="desc svelte-6bql28">Maximum time per line before giving up</span></div> <input type="number" class="num-input svelte-6bql28" min="5" max="300" step="5"/></label></section> <div class="actions svelte-6bql28"><button class="btn svelte-6bql28">Reset to Defaults</button></div></div>');function _r(e,t){Ne(t,!1);const a=()=>J(De,"$settings",s),[s,l]=Oe();function c(){De.set({syntax:!1,syntax_model:"en_core_web_sm",lang:"en",max_syll:18,parse_timeout:30})}Pa();var r=pr(),u=i(v(r),4),f=i(v(u),2),_=i(v(f),2);Ae(_),o(f);var d=i(f,2),m=i(v(d),2),p=v(m);p.value=p.__value="en_core_web_sm";var x=i(p);x.value=x.__value="en_core_web_md";var $=i(x);$.value=$.__value="en_core_web_lg";var N=i($);N.value=N.__value="en_core_web_trf",o(m),o(d),o(u);var b=i(u,2),h=i(v(b),2),D=i(v(h),2),M=v(D);M.value=M.__value="en";var k=i(M);k.value=k.__value="fi",o(D),o(h),o(b);var Y=i(b,2),C=i(v(Y),2),E=i(v(C),2);Ae(E),o(C);var R=i(C,2),z=i(v(R),2);Ae(z),o(R),o(Y);var q=i(Y,2),j=v(q);o(q),o(r),na(_,()=>a().syntax,L=>ke(De,ee(a).syntax=L,ee(a))),dt(m,()=>a().syntax_model,L=>ke(De,ee(a).syntax_model=L,ee(a))),dt(D,()=>a().lang,L=>ke(De,ee(a).lang=L,ee(a))),ft(E,()=>a().max_syll,L=>ke(De,ee(a).max_syll=L,ee(a))),ft(z,()=>a().parse_timeout,L=>ke(De,ee(a).parse_timeout=L,ee(a))),U("click",j,c),T(e,r),qe(),l()}We(["click"]);var br=F("<button><!> <span> </span></button>"),hr=F('<div class="app svelte-12qhfyh"><!> <nav class="top-nav svelte-12qhfyh"><!> <span class="spacer svelte-12qhfyh"></span> <button><!> <span> </span></button></nav> <main class="svelte-12qhfyh"><div><!></div> <div><!></div> <div><!></div> <div><!></div> <div><!></div></main> <!></div>');function Tr(e,t){Ne(t,!0);const a=()=>J(Ct,"$activeTab",s),[s,l]=Oe(),c=[{id:"parse",label:"Parse",icon:Ha},{id:"line",label:"Line",icon:Ga},{id:"meter",label:"Meter",icon:ja},{id:"maxent",label:"MaxEnt",icon:Ba}],r={id:"settings",label:"Settings",icon:Va},u=["parse","line","meter","maxent","settings"],f={parse:0,meter:0,maxent:0,line:0,settings:0};let _=ae(aa(a()));function d(H){const G=H.replace(/^\/+/,"").split("/")[0];return u.includes(G)?G:"parse"}ta(()=>{const H=a();H!==n(_)&&(f[n(_)]=window.scrollY,S(_,H,!0),requestAnimationFrame(()=>window.scrollTo(0,f[H])))}),Ma(async()=>{const H=d(window.location.pathname);ce(Ct,H),S(_,H,!0),history.replaceState({tab:H},"",window.location.pathname),window.addEventListener("popstate",()=>{ce(Ct,d(window.location.pathname))});try{const G=await _n();Oa.set(G.all_constraints),qa.set(G.constraint_descriptions),Na.set(G.defaults.constraints),Ee.update(te=>te.constraints.length===0?{...te,constraints:G.defaults.constraints,max_s:G.defaults.max_s,max_w:G.defaults.max_w,resolve_optionality:G.defaults.resolve_optionality}:te),Ze.update(te=>{const ve={...te};for(const ne of G.all_constraints)ne in ve||(ve[ne]=1);return ve})}catch(G){console.error("Failed to load meter defaults:",G)}});var m=hr(),p=v(m);nn(p);var x=i(p,2),$=v(x);Te($,17,()=>c,H=>H.id,(H,G)=>{var te=br();let ve;var ne=v(te);va(ne,()=>n(G).icon,(oe,pe)=>{pe(oe,{size:16,strokeWidth:1.75})});var le=i(ne,2),ie=v(le,!0);o(le),o(te),K(()=>{ve=he(te,1,"svelte-12qhfyh",null,ve,{active:a()===n(G).id}),I(ie,n(G).label)}),U("click",te,()=>Rt(n(G).id)),T(H,te)});var N=i($,4);let b;var h=v(N);va(h,()=>r.icon,(H,G)=>{G(H,{size:16,strokeWidth:1.75})});var D=i(h,2),M=v(D,!0);o(D),o(N),o(x);var k=i(x,2),Y=v(k);let C;var E=v(Y);On(E,{}),o(Y);var R=i(Y,2);let z;var q=v(R);fr(q,{}),o(R);var j=i(R,2);let L;var X=v(j);Bn(X,{}),o(j);var P=i(j,2);let B;var w=v(P);nr(w,{}),o(P);var y=i(P,2);let O;var g=v(y);_r(g,{}),o(y),o(k);var W=i(k,2);dn(W),o(m),K(()=>{b=he(N,1,"svelte-12qhfyh",null,b,{active:a()===r.id}),I(M,r.label),C=he(Y,1,"tab-panel svelte-12qhfyh",null,C,{hidden:a()!=="parse"}),z=he(R,1,"tab-panel svelte-12qhfyh",null,z,{hidden:a()!=="line"}),L=he(j,1,"tab-panel svelte-12qhfyh",null,L,{hidden:a()!=="meter"}),B=he(P,1,"tab-panel svelte-12qhfyh",null,B,{hidden:a()!=="maxent"}),O=he(y,1,"tab-panel svelte-12qhfyh",null,O,{hidden:a()!=="settings"})}),U("click",N,()=>Rt(r.id)),T(e,m),qe(),l()}We(["click"]);export{Tr as component,kr as universal};
