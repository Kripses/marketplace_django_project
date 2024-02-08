var selector = document.querySelector("input[id='id_phone']");
var im = new Inputmask("+7(999) 999-99-99");

im.mask(selector);

new JustValidate('.contacts__form', {
  rules: {
    name: {
      required: true,
      minLength: 2,
      maxLength: 10
    },
    tel: {
      required: true,
      function: (name, value) => {
        const phone = selector.Inputmask.unmaskedvalue()
        return Number(phone) && phone.length === 10
      }
    },
    // mail: {
    //   required: true,
    //   email: true
    // }
  },
  messages: {
      // name: {
      //   required: 'Как вас зовут?',
      // },
    tel: {
      required: 'Укажите ваш телефон',
    },
    // mail: {
    //   required: 'Укажите ваш e-mail'
    // }
  }
})