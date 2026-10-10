"""Terrain-aware army: a footman screen, covered archers, and charging cavalry."""

from heapq import heappop, heappush

from sandbox.crane import action, me, paths, roster, tile, visible


def key(position):
    return position["q"], position["r"]


class Agent:
    def reset(self, seed, observation):
        self.routes = {}
        self.contacts = {}
        self.outbox = []
        self.round = 0
        self.last_report = -2
        self.friendly_players = {a["player"] for a in roster.allies(observation)}
        self.owners = {a["unit_id"]: a["player"] for a in roster.allies(observation)}
        self.index = int(me.unit_id(observation).rsplit("_", 1)[1])
        self.stalls, self.previous = 0, None

    def _distance_map(self, observation, goal):
        goal_key = key(goal)
        if goal_key in self.routes:
            return self.routes[goal_key]
        grid = observation["observation"]["battlefield"]["tiles"]
        distances, queue = {goal_key: 0}, [(0, goal_key)]
        while queue:
            distance, current = heappop(queue)
            if distance != distances[current]:
                continue
            # Reverse edges: moving toward current pays its terrain cost, not the predecessor's.
            ground = grid[current[1]][current[0]]
            cost = 1 + (ground["terrain"] == "hill") + {"forest": 1, "marsh": 2}.get(ground["feature"], 0)
            for dq, dr in tile.DIRECTIONS.values():
                nxt = current[0] + dq, current[1] + dr
                if not (0 <= nxt[1] < len(grid) and 0 <= nxt[0] < len(grid[nxt[1]])):
                    continue
                if grid[nxt[1]][nxt[0]]["terrain"] in {"void", "water"}:
                    continue
                total = distance + cost
                if total < distances.get(nxt, 10000):
                    distances[nxt] = total
                    heappush(queue, (total, nxt))
        if len(self.routes) > 80:
            self.routes.clear()
        self.routes[goal_key] = distances
        return distances

    def act(self, observation):
        self.round = int(observation["observation"]["round"])
        here, kind = me.position(observation), me.unit_type(observation)
        self.stalls = self.stalls + 1 if self.previous == key(here) else 0
        self.previous = key(here)
        enemies, allies = visible.enemies(observation), visible.allies(observation)
        self.contacts = {k: v for k, v in self.contacts.items() if self.round - v[1] <= 3}
        for enemy in enemies:
            self.contacts[enemy["unit_id"]] = (dict(enemy["position"]), self.round)
        if enemies:
            # Use path cost rather than geometric distance to avoid pursuing across a river.
            target = min(enemies, key=lambda e: self._distance_map(observation, e["position"]).get(key(here), 10000)
                         + (0 if kind == "cavalry" and e["type"] == "archer" else 2)
                         + 0.2 * e["hit_points"])
            goal, target_id = target["position"], target["unit_id"]
            if self.round - self.last_report >= 2:
                text = f"contact|{target_id}|{goal['q']}|{goal['r']}|{self.round}"
                self.outbox = [{"to": self.owners[a["unit_id"]], "text": text} for a in allies]
                self.last_report = self.round
        else:
            target_id = None
            if self.contacts:
                goal, _ = min(self.contacts.values(), key=lambda c: tile.distance(here, c[0]))
            else:
                center = tile.at_center(observation)
                forward = 1 if me.direction(observation) == 2 else -1
                # Do not remain forever at the center after the initial rendezvous.
                advance = min(7, max(0, self.round - 8) // 3)
                lane = (self.index % 3 - 1) * (3 if kind == "cavalry" else 1)
                goal = {"q": center["q"] + forward * advance, "r": center["r"] + lane}
                if tile.terrain_at(observation, goal)["terrain"] in {"void", "water"}:
                    goal = center
        routes = self._distance_map(observation, goal)
        candidates = {}
        for path_id in action.legal_paths(observation):
            end = tile.at_path_end(here, path_id)
            end_key = key(end)
            if end_key not in candidates or len(paths.decode(path_id)) < len(paths.decode(candidates[end_key])):
                candidates[end_key] = path_id
        best, best_score = 0, float("-inf")
        footmen = [a for a in allies if a["type"] == "footman"]
        for end_key, path_id in candidates.items():
            end = {"q": end_key[0], "r": end_key[1]}
            ground = tile.terrain_at(observation, end)["terrain"]
            feature = tile.terrain_at(observation, end)["feature"]
            score = -6 * routes.get(end_key, 10000)
            if enemies:
                distance = tile.distance(end, goal)
                if kind == "archer":
                    reach = 6  # Hills increase vision and damage, not attack range.
                    score = 35 - 5 * abs(distance - (reach - 1)) if 2 <= distance <= reach else -12 * abs(distance - 5)
                    if distance > reach:
                        score -= 3 * routes.get(end_key, 10000)
                    score -= sum(max(0, 4 - tile.distance(end, e["position"])) * 16
                                 for e in enemies if e["type"] != "archer")
                    score += (3 if ground == "hill" else 0) + (2 if feature == "forest" else 0)
                    score += 2 if any(tile.distance(end, a["position"]) <= 2 for a in footmen) else 0
                else:
                    score += 35 if distance <= 1 else 0
                    if kind == "cavalry" and distance <= 1 and tile.distance(here, end) >= 3:
                        score += 9 if tile.terrain_at(observation, goal)["feature"] != "forest" else 0
                    if kind == "footman" and any(tile.distance(end, a["position"]) == 1 for a in footmen):
                        score += 3
                    score += 1 if feature == "forest" else 0
            elif kind == "archer" and footmen:
                # Approach contact behind the nearest screen, not ahead of it.
                score -= 1.5 * min(abs(tile.distance(end, a["position"]) - 2) for a in footmen)
            score -= 0.05 * len(paths.decode(path_id))
            if self.stalls >= 3 and path_id == 0 and not enemies:
                score -= 8
            if score > best_score:
                best, best_score = path_id, score
        return action.move(best, target_id, observation)

    def chat(self, inbox):
        for message in inbox:
            if message.get("from") not in self.friendly_players:
                continue
            parts = message.get("text", "").split("|")
            if len(parts) != 5 or parts[0] != "contact":
                continue
            try:
                q, r, tick = map(int, parts[2:])
            except ValueError:
                continue
            if 0 <= q <= 24 and 0 <= r <= 24 and 0 <= self.round - tick <= 3:
                self.contacts[parts[1]] = ({"q": q, "r": r}, tick)
        result, self.outbox = self.outbox, []
        return result or None
