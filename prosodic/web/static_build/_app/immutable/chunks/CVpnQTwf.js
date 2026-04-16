import{c as m,u as b,d as h,e as w,r as u,f as y,g,h as _,i as x,w as n}from"./BPpoBFJ_.js";function L(e=!1){const t=m,s=t.l.u;if(!s)return;let a=()=>_(t.s);if(e){let i=0,r={};const p=x(()=>{let f=!1;const l=t.s;for(const c in l)l[c]!==r[c]&&(r[c]=l[c],f=!0);return f&&i++,i});a=()=>g(p)}s.b.length&&b(()=>{d(t,a),u(s.b)}),h(()=>{const i=w(()=>s.m.map(y));return()=>{for(const r of i)typeof r=="function"&&r()}}),s.a.length&&h(()=>{d(t,a),u(s.a)})}function d(e,t){if(e.l.s)for(const s of e.l.s)g(s);t()}const T=`From fairest creatures we desire increase,
That thereby beauty's rose might never die,
But as the riper should by time decease,
His tender heir might bear his memory:
But thou, contracted to thine own bright eyes,
Feed'st thy light'st flame with self-substantial fuel,
Making a famine where abundance lies,
Thyself thy foe, to thy sweet self too cruel.
Thou that art now the world's fresh ornament
And only herald to the gaudy spring,
Within thine own bud buriest thy content
And, tender churl, makest waste in niggarding.
Pity the world, or else this glutton be,
To eat the world's due, by the grave and thee.`;function v(e,t){try{const s=localStorage.getItem(e);return s?JSON.parse(s):t}catch{return t}}function o(e,t){const s=n(v(e,t));return s.subscribe(a=>{localStorage.setItem(e,JSON.stringify(a))}),s}const W=o("prosodic:text",T),k=o("prosodic:meter",{constraints:[],max_s:2,max_w:2,resolve_optionality:!0}),C=o("prosodic:weights",{}),A=o("prosodic:zoneWeights",null),F=o("prosodic:maxent",{target_scansion:"wswswswsws",zones:3,regularization:100,syntax:!1}),S=o("prosodic:tab","parse");function J(e){{const t=e==="parse"?"/":`/${e}`;window.location.pathname!==t&&history.pushState({tab:e},"",t)}S.set(e)}const N=n([]),O=n({}),B=n([]),D=n(!1),E=n(null),I=n(!1),j=n([]),H=n(null),M=o("prosodic:settings",{syntax:!1,syntax_model:"en_core_web_sm",lang:"en",max_syll:18,parse_timeout:30});export{S as a,W as b,C as c,F as d,j as e,H as f,J as g,B as h,L as i,O as j,N as k,I as l,k as m,E as n,D as p,M as s,A as z};
