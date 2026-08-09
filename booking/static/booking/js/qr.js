/* helper กลางสำหรับวาด QR code ทุกช่องทางของระบบ (/card/, /card-login/, /external/,
 * /external/permanent/, /manage/external/<id>/)
 *
 * เดิมแต่ละหน้า hardcode ขนาดไว้คนละค่า (160/180/200 px) ซึ่งเล็กเกินไปเวลาสแกนที่ประตู
 * โดยเฉพาะบนมือถือที่หน้าจอสว่างไม่พอหรือถือห่างจากเครื่องอ่าน — รวมมาไว้ที่นี่ที่เดียว
 * เพิ่ม/ลดขนาดทั้งระบบให้แก้ที่ MIN_PX / MAX_PX
 *
 * ขนาดคิดจากความกว้างจอจริง ไม่ใช่ค่าคงที่ เพื่อให้ QR ใหญ่เต็มที่เท่าที่กล่องรองรับได้
 * แล้ววาดที่ความละเอียด 2 เท่า (retina) ก่อนย่อด้วย CSS ให้ขอบโมดูลคมบนจอความละเอียดสูง
 *
 * ใช้:  NPUQr.render(el, text, { reserve: 88, max: 320, colorDark: '#0d1f3c' })
 *   reserve = ผลรวม padding/margin รอบ ๆ ที่กินพื้นที่ไปจากความกว้างจอ (คิดของแต่ละหน้าเอง)
 */
(function (global) {
    'use strict';

    var MIN_PX = 200;   // เล็กสุดที่ยังสแกนติดบนจอมือถือเก่า
    var MAX_PX = 320;   // ใหญ่สุด กันล้นกล่องบนจอกว้าง
    var CONTAINER_CAP = 500;   // ทุกหน้าจำกัดความกว้างเนื้อหาไว้ ~480px อยู่แล้ว
    var SAFETY_PX = 8;         // กันล้นแนวนอนเมื่อ reserve คำนวณพอดีเป๊ะ (scrollbar/เส้นขอบ)

    function sizeFor(reserve, max) {
        var avail = Math.min(global.innerWidth || CONTAINER_CAP, CONTAINER_CAP)
                    - (reserve || 0) - SAFETY_PX;
        return Math.max(MIN_PX, Math.min(max || MAX_PX, Math.floor(avail)));
    }

    /* qrcodejs วาดลง <canvas> แล้ว "สลับ" เป็น <img> (ซ่อน canvas) ซึ่งอาจเกิดทีหลัง
     * การไล่ตั้ง style รายตัวจึงพลาดได้ถ้า <img> ถูกสร้างหลังเราตั้งค่าไปแล้ว —
     * คุมด้วย CSS ที่ตัวครอบแทน ลูกทุกตัวที่โผล่มาทีหลังจะถูกบังคับขนาดเองอัตโนมัติ
     * (ห้ามแตะ display เพราะ canvas ที่ถูกซ่อนไว้จะกลับมาโผล่ซ้อนกับ img) */
    var STYLE_ID = 'npu-qr-style';

    function ensureStyle() {
        if (global.document.getElementById(STYLE_ID)) { return; }
        var st = global.document.createElement('style');
        st.id = STYLE_ID;
        st.textContent = '[data-npu-qr]>canvas,[data-npu-qr]>img' +
                         '{width:100%!important;height:auto!important;}';
        global.document.head.appendChild(st);
    }

    function render(el, text, opts) {
        if (!el || !text) { return 0; }
        opts = opts || {};

        var px = sizeFor(opts.reserve, opts.max);
        ensureStyle();
        el.innerHTML = '';
        el.setAttribute('data-npu-qr', '');
        el.style.width = px + 'px';
        el.style.lineHeight = '0';       // กันช่องว่างใต้ภาพจาก baseline ของ inline element
        new global.QRCode(el, {
            text: text,
            width: px * 2,
            height: px * 2,
            colorDark: opts.colorDark || '#0d1f3c',
            colorLight: opts.colorLight || '#ffffff',
            correctLevel: global.QRCode.CorrectLevel.M,
        });

        return px;
    }

    global.NPUQr = { render: render, sizeFor: sizeFor };
}(window));
