# ROLE_DEFS = {
#    "KEY": (Name, isEvil, Description, ShownToMerlin, ShownToPercival, ShownToEvil, ShownToServant)
# }

NAME, IS_EVIL, DESC, TO_MERLIN, TO_PERCIVAL, TO_EVIL, TO_SERVANT = range(7)

ROLE_DEFS = {
    "MERLIN":   ("Merlin", False, "Knows Evil (except Mordred)", False, True,  False, False),
    "PERCIVAL": ("Percival", False, "Knows Merlin/Morgana",      False, False, False, False),
    "SERVANT":  ("Loyal Servant", False, "No special knowledge", False, False, False, False),
    "ASSASSIN": ("Assassin", True, "Can kill Merlin at end",    True,  False, True,  False),
    "MORGANA":  ("Morgana", True, "Appears as Merlin to Percival",True,  True,  True,  False),
    "MORDRED":  ("Mordred", True, "Hidden from Merlin",         False, False, True,  False),
    "OBERON":   ("Oberon", True, "Blind to other Evil",         True,  False, False, False),
    "MINION":   ("Minion of Mordred", True, "Generic bad guy",  True,  False, True,  False)
}

# The "Rulebook": Mapping Player Count to Mission Requirements
# Format: { TotalPlayers: {"team": (Good, Evil), "sizes": [M1..M5], "fails": [M1..M5]} }
GAME_RULES = {
    5: {
        "team": (3, 2),
        "sizes": [2, 3, 2, 3, 3],
        "fails": [1, 1, 1, 1, 1]
    },
    6: {
        "team": (4, 2),
        "sizes": [2, 3, 4, 3, 4],
        "fails": [1, 1, 1, 1, 1]
    },
    7: {
        "team": (4, 3),
        "sizes": [2, 3, 3, 4, 4],
        "fails": [1, 1, 1, 2, 1]  # <--- Mission 4 requires 2 fails
    },
    8: {
        "team": (5, 3),
        "sizes": [3, 4, 4, 5, 5],
        "fails": [1, 1, 1, 2, 1]
    },
    9: {
        "team": (6, 3),
        "sizes": [3, 4, 4, 5, 5],
        "fails": [1, 1, 1, 2, 1]
    },
    10: {
        "team": (6, 4),
        "sizes": [3, 4, 4, 5, 5],
        "fails": [1, 1, 1, 2, 1]
    }
}
