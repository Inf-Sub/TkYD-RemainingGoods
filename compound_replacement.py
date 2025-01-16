__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.7.7'


from typing import Dict

def get_dict_replacements() -> Dict[str, str]:
    return {
        'П/Э': 'Полиэстер',
        'П/А': 'Полиамид',
        'метанить': 'Металлизированная нить',
        'альпаки': 'альпака',
        
    }