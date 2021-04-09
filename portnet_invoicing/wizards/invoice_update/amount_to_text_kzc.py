# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

#-------------------------------------------------------------
# French
#-------------------------------------------------------------


to_19_fr = ( 'zéro',  'un',   'deux',  'trois', 'quatre',   'cinq',   'six',
          'sept', 'huit', 'neuf', 'dix',   'onze', 'douze', 'treize',
          'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf' )
tens_fr  = ( 'vingt', 'trente', 'quarante', 'Cinquante', 'Soixante', 'Soixante-dix', 'Quatre-vingts', 'Quatre-vingt-dix')
denom_fr = ( '',
          'Mille',     'Millions',         'Milliards',       'Billions',       'Quadrillions',
          'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
          'Décillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
          'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Icosillion', 'Vigintillion' )

to_7n_fr = ('soixante et onze','soixante-douze','soixante-treize', 'soixante-quatorze', 'soixante-quinze',
             'soixante-seize', 'soixante-dix-sept', 'soixante-dix-huit', 'soixante-dix-neuf')

to_8n_fr = ('quatre-vingt-un','quatre-vingt-deux','quatre-vingt-trois', 'quatre-vingt-quatre', 'quatre-vingt-cinq',
             'quatre-vingt-six', 'quatre-vingt-sept', 'quatre-vingt-huit', 'quatre-vingt-neuf')

to_9n_fr = ('quatre-vingts et onze','quatre-vingts-douze','quatre-vingts-treize', 'quatre-vingts-quatorze', 'quatre-vingts-quinze',
             'quatre-vingts-seize', 'quatre-vingts-dix-sept', 'quatre-vingts-dix-huit', 'quatre-vingts-dix-neuf')

# convert a value < 100 to French.

def _convert_nn_fr(val):
    if val < 20:
        return to_19_fr[val]
    if val > 70 and val < 80 :
       return to_7n_fr[val-71]
    if val > 80 and val < 90 :
       return to_8n_fr[val-81]
    if val > 90 and val < 100 :
       return to_9n_fr[val-91] 
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_fr)):
        if dval + 10 > val:
            if val % 10:
                if val -(val % 10) == 80 :
                    return 'Quatre-vingt' + '-' + to_19_fr[val % 10]
                return dcap + '-' + to_19_fr[val % 10]
            return dcap

def _convert_nnn_fr(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        
        if mod == 0 :
            if to_19_fr[rem] =='un':
                word=' Cent'
                
            else :
                
                word = to_19_fr[rem] + ' Cents'
               
        else :
           
            if rem == 1 :
                word = 'Cent'
            else :
                word = to_19_fr[rem] + ' Cent'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn_fr(mod)
    return word


def french_number(val):
    if val < 100:
        return _convert_nn_fr(val)
    if val < 1000:
         return _convert_nnn_fr(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_fr))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if (val // 1000000) == 1 :
                ret = _convert_nnn_fr(l) + ' ' + 'Million'
            else :
                if _convert_nnn_fr(l) == 'un' and denom_fr[didx] == 'Mille':
                    ret = denom_fr[didx]
                else :
                    ret = _convert_nnn_fr(l) + ' ' + denom_fr[didx]
            if r > 0:
                ret = ret + ' ' + french_number(r)
            return ret

def amount_to_text_fr(number, currency):
    number = '%.2f' % number
    list = str(number).split('.')
    start_word = french_number(int(list[0]))
    end_word = french_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and ' centimes' or ' centime'
    res = start_word.lower() +' '+ str(currency) +' et '+ end_word +' '+ cents_name+' TTC'
    return res

#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------
# from tools.translate import _

to_19 = ( 'zero',  'one',   'two',  'three', 'four',   'five',   'six',
          'seven', 'eight', 'nine', 'ten',   'eleven', 'twelve', 'thirteen',
          'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen' )
tens  = ( 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety')
denom = ( '',
          'thousand',     'million',         'billion',       'trillion',       'quadrillion',
          'quintillion',  'sextillion',      'septillion',    'octillion',      'nonillion',
          'decillion',    'undecillion',     'duodecillion',  'tredecillion',   'quattuordecillion',
          'sexdecillion', 'septendecillion', 'octodecillion', 'novemdecillion', 'vigintillion' )

# convert a value < 100 to English.
def _convert_nn(val):
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19[val % 10]
            return dcap

# convert a value < 1000 to english, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' Hundred'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod)
    return word

def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
         return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ', ' + english_number(r)
            return ret

def amount_to_text(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'cents' or 'cent'
    final_result = start_word.capitalize() +' '+units_name+' and ' + end_word +' '+cents_name+' TTC'
    print final_result
    return final_result


#-------------------------------------------------------------
# Dutch
#-------------------------------------------------------------

to_19_nl = ( 'Nul',  'Een',   'Twee',  'Drie', 'Vier',   'Vijf',   'Zes',
          'Zeven', 'Acht', 'Negen', 'Tien',   'Elf', 'Twaalf', 'Dertien',
          'Veertien', 'Vijftien', 'Zestien', 'Zeventien', 'Achttien', 'Negentien' )
tens_nl  = ( 'Twintig', 'Dertig', 'Veertig', 'Vijftig', 'Zestig', 'Zeventig', 'Tachtig', 'Negentig')
denom_nl = ( '',
          'Duizend', 'Miljoen', 'Miljard', 'Triljoen', 'Quadriljoen',
           'Quintillion', 'Sextiljoen', 'Septillion', 'Octillion', 'Nonillion',
           'Decillion', 'Undecillion', 'Duodecillion', 'Tredecillion', 'Quattuordecillion',
           'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )

# convert a value < 100 to Dutch.
def _convert_nn_nl(val):
    if val < 20:
        return to_19_nl[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_nl)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19_nl[val % 10]
            return dcap

# convert a value < 1000 to Dutch, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn_nl(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19_nl[rem] + ' Honderd'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn_nl(mod)
    return word

def dutch_number(val):
    if val < 100:
        return _convert_nn_nl(val)
    if val < 1000:
         return _convert_nnn_nl(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_nl))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn_nl(l) + ' ' + denom_nl[didx]
            if r > 0:
                ret = ret + ', ' + dutch_number(r)
            return ret

def amount_to_text_nl(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = dutch_number(int(list[0]))
    end_word = dutch_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'cent' or 'cent'
    final_result = start_word +' '+units_name+' '+ end_word +' '+cents_name
    return final_result

#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'nl' : amount_to_text_nl, 'fr' : amount_to_text_fr, 'en' : amount_to_text}

def add_amount_to_text_function(lang, func):
    _translate_funcs[lang] = func
    
#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='fr', currency='Dirhams'):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: mille six cent cinquante-quatre.
    """
#    if nbr > 1000000:
##TODO: use logger   
#        print "WARNING: number too large '%d', can't translate it!" % (nbr,)
#        return str(nbr)
    
    if not _translate_funcs.has_key(lang):
#TODO: use logger   
        print "WARNING: no translation function found for lang: '%s'" % (lang,)
#TODO: (default should be en) same as above
        lang = 'fr'
    return _translate_funcs[lang](abs(nbr), currency)

if __name__=='__main__':
    from sys import argv
    
    lang = 'nl'
    if len(argv) < 2:
        for i in range(1,200):
            print i, ">>", amount_to_text(i, lang)
        for i in range(200,999999,139):
            print i, ">>", amount_to_text(i, lang)
    else:
        print amount_to_text(int(argv[1]), lang)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

