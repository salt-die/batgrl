// setting highlight for async stuff in python
var async_kw = ['async', 'await'];
jQuery.each(async_kw, function(i, kw){
  var elements = jQuery(".highlight-python .n:contains('" + kw + "')");

  jQuery.each(elements, function(j, el){
    el = jQuery(el);
    if (el.text() == kw){
      el.removeClass('n');
      el.addClass('kn');
    };
  });
});
