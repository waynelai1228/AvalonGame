import communications as comm
import constants

class Player:
    def __init__(self, name, connection_id):
        # 1. Identity
        self.name = name
        self.connection_id = connection_id  # Pipe name, Socket, or UserID
        
        # 2. Role Information
        self.role = None        # e.g., "MERLIN", "PERCIVAL", "SERVANT"
        self.is_evil = False    # Quick flag for logic checks
        
        # 3. Vision / Hidden Knowledge
        # Stores what this specific player sees (e.g., {"Bob": "EVIL"})
        self.seen_players = {} 
        
        # 4. Status
        self.is_leader = False
        self.on_current_mission = False

    def assign_role(self, role):
        """Sets the player's role and alignment."""
        self.role = role
        self.is_evil = constants.ROLE_DEFS[role][constants.IS_EVIL]

    def add_vision(self, player_name, appearance):
        """Adds knowledge about another player (e.g., 'Evil' or 'Merlin/Morgana')."""
        self.seen_players[player_name] = appearance

    def get_vision_report(self):
        """Formats the secret info to be sent via private message."""
        if not self.seen_players:
            return "You have no special knowledge."
        
        report = "Your Vision:\n"
        for name, identity in self.seen_players.items():
            report += f"- {name}: {identity}\n"
        return report

    def __repr__(self):
        return f"<Player {self.name} ({self.role})>"


class AvalonGame:
    def __init__(self, player_names, comm_interface):
        # 1. Communication & Players
        self.comm = comm_interface  # Your pluggable Comm object
        self.players = player_names  # List of names
        self.roles = {}              # { "Alice": "Merlin", "Bob": "Assassin" }
        
        # 2. Mission Tracking
        self.current_mission = 1     # 1 through 5
        self.mission_results = []    # List of Booleans (True=Success, False=Fail)
        self.failed_proposals = 0    # "Vote Track" (reaches 5 = Evil wins mission)
        
        # 3. Turn Management
        self.leader_index = 0        # Index of player currently proposing
        self.current_team = []       # Players nominated for the current mission
        self.game_over = False
        
        # 4. Configuration (Standard 5-10 player Avalon rules)
        # Requirements for each mission based on player count
        self.mission_requirements = self._get_mission_configs(len(player_names))

    # --- CORE GAME LOOP ---
    def start_game(self):
        """Initializes roles and starts the main loop."""
        self._assign_roles()
        self._inform_players() # The 'Vision' phase (Merlin sees Minions, etc.)
        
        while not self.game_over:
            self.run_proposal_phase()
            self.run_voting_phase()
            self.check_win_conditions()

    # --- PHASE FUNCTIONS ---
    def run_proposal_phase(self):
        """Leader selects a team of a specific size."""
        leader = self.players[self.leader_index]
        req_size = self.mission_requirements[self.current_mission - 1]
        
        self.comm.broadcast(f"LEADER: {leader} is proposing a team of {req_size}.")
        # Use your poll interface to get names from the leader
        self.current_team = self.comm.poll(voters=[leader], count=req_size)

    def run_voting_phase(self):
        """Whole group votes publicly on the proposed team."""
        self.comm.broadcast(f"Proposed Team: {', '.join(self.current_team)}. Vote YES/NO.")
        votes = self.comm.poll(voters=self.players) # Public poll
        
        if self._count_votes(votes) > (len(self.players) / 2):
            self.comm.broadcast("Proposal Accepted!")
            self.failed_proposals = 0
            self.run_mission_phase()
        else:
            self.failed_proposals += 1
            self.comm.broadcast(f"Proposal Rejected. Vote Track: {self.failed_proposals}/5")
            self._rotate_leader()
            if self.failed_proposals >= 5:
                self._force_mission_fail()

    def run_mission_phase(self):
        """The nominated team votes secretly (Success/Fail)."""
        self.comm.broadcast("Mission is underway. Waiting for secret votes...")
        results = self.comm.poll(voters=self.current_team, secret=True)
        
        # Count fails (Mission 4 with 7+ players requires TWO fails)
        fail_count = results.count("Fail")
        if fail_count >= self._fails_required():
            self.mission_results.append(False)
            self.comm.broadcast(f"Mission {self.current_mission} FAILED! ({fail_count} Fails)")
        else:
            self.mission_results.append(True)
            self.comm.broadcast(f"Mission {self.current_mission} SUCCEEDED!")
        
        self.current_mission += 1
        self._rotate_leader()

    def run_assassination_phase(self):
        """Final state if Good wins 3 missions."""
        assassin = [p for p, r in self.roles.items() if r == "Assassin"][0]
        self.comm.broadcast("Good has won 3 missions! Assassin, name Merlin to win.")
        target = self.comm.poll(voters=[assassin], count=1)
        
        if self.roles[target] == "Merlin":
            self.comm.broadcast("Assassin found Merlin! EVIL WINS.")
        else:
            self.comm.broadcast("Assassin missed! GOOD WINS.")
        self.game_over = True

    # --- INTERNAL HELPERS ---
    def _assign_roles(self):
        """Logic for shuffling and assigning Avalon roles."""
        pass

    def _inform_players(self):
        """The critical 'Knowledge' phase using private comm.send()."""
        # Logic: if player == Merlin, send list of Minions, etc.
        pass

    def check_win_conditions(self):
        """Checks if either side has won 3 missions."""
        if self.mission_results.count(True) >= 3:
            self.run_assassination_phase()
        elif self.mission_results.count(False) >= 3:
            self.comm.broadcast("Evil has sabotaged 3 missions. EVIL WINS.")
            self.game_over = True


def main():
    comm.handle_connections(10000)
    p1 = Player("Alice", "Merlin")
    p1.assign_role("OBERON")
    print(p1.is_evil)
    print(constants.ROLE_DEFS)
    print(constants.GAME_RULES)


if __name__ == '__main__':
    main()
