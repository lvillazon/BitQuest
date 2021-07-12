unit_words=['','one','two','three','four','five',
'six','seven','eight', 'nine']
tens_words=['', '', 'twenty','thirty','forty','fifty',
'sixty','seventy','eighty', 'ninety']
teens_words=['ten','eleven','twelve','thirteen','fourteen','fifteen',
'sixteen','seventeen', 'eighteen', 'nineteen']
units = data % 10
tens = data // 10
if tens == 0:
    print(unit_words[units])
elif tens == 1:
    print(teens_words[units])
else:
    print(tens_words[tens],unit_words[units])
