import{w as t}from"./CTmTAdiN.js";const r=`From fairest creatures we desire increase,
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
To eat the world's due, by the grave and thee.`;function i(n,o){try{const s=localStorage.getItem(n);return s?JSON.parse(s):o}catch{return o}}function e(n,o){const s=t(i(n,o));return s.subscribe(a=>{localStorage.setItem(n,JSON.stringify(a))}),s}const h=e("prosodic:text",r),l=e("prosodic:meter",{constraints:[],max_s:2,max_w:2,resolve_optionality:!0}),d=e("prosodic:weights",{}),u=e("prosodic:zoneWeights",null),g=e("prosodic:maxent",{target_scansion:"wswswswsws",zones:3,regularization:100,syntax:!1}),m=e("prosodic:tab","parse"),w=t([]),f=t({}),p=t([]),y=t(!1),b=t(null),x=t(!1),T=t([]),v=t(null);export{m as a,g as b,T as c,d,p as e,f,w as g,x as h,h as i,b as j,l as m,y as p,v as s,u as z};
