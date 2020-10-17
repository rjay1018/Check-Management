# -*- coding: utf-8 -*-


from odoo.tools.translate import _
"""  
To manage amount to arabic for foreign purchase 
"""
to_19 = (u'صفر',u'واحد',u'إثنان',u'ثلاثة',u'أربعة',u'خمسة',u'ستة',u'سبعة',u'ثمانية',u'تسعة',u'عشرة',u'أحدعشر',u'إثناعشر',u'ثلاثةعشر',u'أربعةعشر',u'خمسةعشر',u'ستةعشر',u'سبعةعشر',u'ثمانيةعشر',u'تسعةعشر')
tens  = (u'عشرون',u'ثلاثون',u'أربعون',u'خمسون',u'ستون',u'سبعون',u'ثمانون',u'تسعون')
hundreds=('',u'مائـة',u'مائتـان',u'ثلاثمـائة',u'أربعمـائة',u'خمسمـائة',u'ستمائة',u'سبعمائة',u'ثمانمائة',u'تسعمائة')
denom = ('',u'الف',u'مليون',u'مليار',u'تريليون')

# convert a value < 100 to English.
def _convert_nn(val):
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return  to_19[val % 10]+u' و ' +dcap 
            return dcap

# convert a value < 1000 to english, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = mod > 0 and hundreds[rem] + u' و ' or  hundreds[rem] #to_19[rem] + u' مائة'

    if mod > 0:
        word = word+' '+_convert_nn(mod)
    return word

def english_number(val):
    if val < 1000:
        return val < 100 and _convert_nn(val) or  _convert_nnn(val)
    
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l)  +' '+ denom[didx]
            ret = r > 0 and ret + ' '+u' و ' + english_number(r) or ret
            return ret

def amount_to_text(number, units_name=u'جنيه', cents_name=u'قرش'):
    number = '%.2f' % number
    list = str(number).split('.')
    #start_word + units_name
    final_result =  u' فقط ' + (english_number(int(list[0])) or ' ') + ' '+ (units_name or ' ')
    if int(list[1]) >0:
    	#final_result = end_word + cents_name (if cents_number <> ZERO)
    	final_result +=  u' و ' + (english_number(int(list[1])) or ' ') +'  '+((int(list[1]) != 0) and cents_name or ' ' + u' لا غير ')
    return final_result+ u' لا غير '


#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'ar' : amount_to_text}
    
#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='ar', units_name=u'جنيه', cents_name=u'قرش'):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: thousands six cent cinquante-quatre.
    """
    from odoo import netsvc
    import logging
    _logger = logging.getLogger(__name__)
#    if nbr > 10000000:
#        netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("Number too large '%d', can not translate it"))
#        return str(nbr)
    
    if 'lang' not in _translate_funcs:
        #v11
        _logger.warning("no translation function found for lang: '%s'", lang)
        #netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("no translation function found for lang: '%s'" % (lang,)))
        #TODO: (default should be en) same as above
        lang = 'ar'
    return _translate_funcs[lang](abs(nbr), units_name, cents_name)

if __name__=='__main__':
    from sys import argv
    
    lang = 'ar'
    if len(argv) < 2:
        for i in range(1,200):
            l = int_to_text(i, lang)
        for i in range(200,999999,139):
            l = int_to_text(i, lang)
    else:
        l = int_to_text(int(argv[1]), lang)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
