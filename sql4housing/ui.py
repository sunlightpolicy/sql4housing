def header(header_str, color=''):
    print('\n\033[1m%s%s\033[0m' % (color, header_str))


def item(item_str):
	try:
    	print('  ▶ %s' % item_str)
    except UnicodeEncodeError:
    	print('  - %s' % item_str)
