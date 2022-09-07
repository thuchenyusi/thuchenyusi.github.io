---
layout: post
title:  "读过的推理书"
author: 卡夫卡的K
date:   2022-09-07 23:05:29 +0800
categories: book detective
---
# 书单
- [ 福尔摩斯探案全集（上中下） ](https://book.douban.com/subject/1040211/)
- [ 布朗神父探案全集（上下） ](https://book.douban.com/subject/3035311/)
- [ 罗杰疑案 ](https://book.douban.com/subject/1807516/)
- [ 东方快车谋杀案 ](https://book.douban.com/subject/1827374/)
- [ 中国橘子之谜 ](https://book.douban.com/subject/23778063/)
- [ 三口棺材 ](https://book.douban.com/subject/30324991/)
- [ ABC谋杀案 ](https://book.douban.com/subject/1903164/)
- [ 尼罗河上的惨案 ](https://book.douban.com/subject/1818347/)
- [ 犹大之窗 ](https://book.douban.com/subject/30441962/)
- [ 扭曲的铰链 ](https://book.douban.com/subject/30323994/)
- [ 无人生还 ](https://book.douban.com/subject/3006581/)
- [ 阳光下的罪恶 ](https://book.douban.com/subject/1805514/)
- [ 捕鼠器 ](https://book.douban.com/subject/10539805/)
- [ 时间的女儿 ](https://book.douban.com/subject/19977987/)
- [ 点与线·零的焦点 ](https://book.douban.com/subject/2335749/)
- [ 大唐狄公案 ](https://book.douban.com/subject/1755295/)
- [ 大唐狄公案 ](https://book.douban.com/subject/1755293/)
- [ 大唐狄公案 ](https://book.douban.com/subject/1755300/)
- [ 大唐狄公案 ](https://book.douban.com/subject/1755296/)
- [ 砂器 ](https://book.douban.com/subject/2119536/)
- [ 十角馆事件 ](https://book.douban.com/subject/26771717/)
- [ 有翼之暗 ](https://book.douban.com/subject/25892396/)
- [ 钟表馆事件 ](https://book.douban.com/subject/25848819/)
- [ 解体诸因 ](https://book.douban.com/subject/4277347/)
- [ 狱门岛 ](https://book.douban.com/subject/11614712/)
- [ 恶魔吹着笛子来 ](https://book.douban.com/subject/11597271/)
- [ 占星术杀人魔法 ](https://book.douban.com/subject/3187737/)
- [ 北方夕鹤2/3杀人事件 ](https://book.douban.com/subject/20468727/)
- [ 斜屋犯罪 ](https://book.douban.com/subject/3187750/)
- [ 奇想，天动 ](https://book.douban.com/subject/23780806/)
- [ 异邦骑士 ](https://book.douban.com/subject/3615048/)
- [ X的悲剧 ](https://book.douban.com/subject/3347997/)
- [ Y的悲剧 ](https://book.douban.com/subject/3348010/)
- [ Z的悲剧 ](https://book.douban.com/subject/3348024/)
- [ 本阵杀人事件 ](https://book.douban.com/subject/11528304/)
- [ 希腊棺材之谜 ](https://book.douban.com/subject/3112726/)
- [ 埃及十字架之谜 ](https://book.douban.com/subject/26808302/)
- [ 东京空港杀人案 ](https://book.douban.com/subject/2027672/)
- [ 刺青杀人事件 ](https://book.douban.com/subject/10518843/)
- [ 只有猫知道 ](https://book.douban.com/subject/6712851/)
- [ 第七重解答 ](https://book.douban.com/subject/4140380/)
- [ 哲瑞·雷恩的最后一案 ](https://book.douban.com/subject/26915347/)
- [ 全部成为F ](https://book.douban.com/subject/4836934/)
- [ 高层饭店的死角 ](https://book.douban.com/subject/2257354/)
- [ 恶意 ](https://book.douban.com/subject/3646172/)
- [ 诗人 ](https://book.douban.com/subject/1948429/)
- [ 嫌疑人X的献身 ](https://book.douban.com/subject/3211779/)
- [ 人骨拼图 ](https://book.douban.com/subject/5480973/)
- [ 斯泰尔斯庄园奇案 ](https://book.douban.com/subject/1946666/)
- [ 一朵桔梗花 ](https://book.douban.com/subject/5269222/)
- [ 黑色皮箱 ](https://book.douban.com/subject/10549915/)
- [ 追捕 ](https://book.douban.com/subject/25786883/)
- [ 真相 ](https://book.douban.com/subject/6019121/)
- [ 金色梦乡 ](https://book.douban.com/subject/5038409/)
- [ 宵待草夜情 ](https://book.douban.com/subject/26367367/)
- [ 玫瑰的名字 ](https://book.douban.com/subject/3836566/)
- [ 独眼少女 ](https://book.douban.com/subject/25918073/)

# 代码
```javascript
var str = "";
for (let x of document.getElementsByClassName("title")) {
    element = x.getElementsByTagName("a").item(0);
    str += "-[! [" + element.innerHTML + "]("+ element.getAttribute("href") +")]("++")<br>";
}
document.write(str);
```