package info.riemannhypothesis.dixit.server.objects;

import java.util.HashMap;
import java.util.Map;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Match {

    public static final int      STANDARD_TIMEOUT = 60 * 60 * 24; // 24h

    private long                 id;

    private Player[]             players;
    private Round[]              rounds;

    private int                  totalRounds;
    private int                  currentRound;

    private Map<Player, Integer> standings;

    private int                  timeout;

    public Match() {
        id = (long) (Math.random() * Long.MAX_VALUE);
    }

    public Match(Player[] players) {
        id = (long) (Math.random() * Long.MAX_VALUE);
        this.players = players;
        totalRounds = players.length;
        currentRound = 0;
        rounds = new Round[totalRounds];
        standings = new HashMap<Player, Integer>();
        timeout = STANDARD_TIMEOUT;
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public Player[] getPlayers() {
        return players;
    }

    public void setPlayers(Player[] players) {
        this.players = players;
    }

    public Round[] getRounds() {
        return rounds;
    }

    public void setRounds(Round[] rounds) {
        this.rounds = rounds;
    }

    public int getTotalRounds() {
        return totalRounds;
    }

    public void setTotalRounds(int totalRounds) {
        this.totalRounds = totalRounds;
    }

    public int getCurrentRound() {
        return currentRound;
    }

    public void setCurrentRound(int currentRound) {
        this.currentRound = currentRound;
    }

    public Map<Player, Integer> getStandings() {
        return standings;
    }

    public void setStandings(Map<Player, Integer> standings) {
        this.standings = standings;
    }

    public int getTimeout() {
        return timeout;
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

}
