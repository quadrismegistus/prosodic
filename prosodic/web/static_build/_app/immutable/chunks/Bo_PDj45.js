import{a8 as o}from"./p0UAk4eg.js";const c=[...` 	
\r\f \v\uFEFF`];function f(e,r,s){var t=e==null?"":""+e;if(s){for(var a of Object.keys(s))if(s[a])t=t?t+" "+a:a;else if(t.length)for(var h=a.length,n=0;(n=t.indexOf(a,n))>=0;){var l=n+h;(n===0||c.includes(t[n-1]))&&(l===t.length||c.includes(t[l]))?t=(n===0?"":t.substring(0,n))+t.substring(l+1):n=l}}return t===""?null:t}function m(e,r){return e==null?null:String(e)}const u=`From fairest creatures we desire increase,
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
To eat the world's due, by the grave and thee.`;function g(e,r){try{const s=localStorage.getItem(e);return s?JSON.parse(s):r}catch{return r}}function i(e,r){const s=o(g(e,r));return s.subscribe(t=>{localStorage.setItem(e,JSON.stringify(t))}),s}const w=i("prosodic:text",u),p=i("prosodic:meter",{constraints:[],max_s:2,max_w:2,resolve_optionality:!0}),y=i("prosodic:weights",{}),b=i("prosodic:zoneWeights",null),x=i("prosodic:maxent",{target_scansion:"wswswswsws",zones:3,regularization:100,syntax:!1}),T=o([]),_=o({}),S=o([]),v=o(!1),z=o(null),O=o(!1),W=o([]);export{y as a,_ as b,W as c,S as d,T as e,m as f,x as g,z as h,w as i,O as j,p as m,v as p,f as t,b as z};
