package info.riemannhypothesis.dixit.server;

import java.util.List;
import java.util.Map;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Match {

    private long                 id;

    private Player[]             players;
    private Round[]              rounds;

    private int                  totalRounds;
    private int                  currentRound;

    private Map<Player, Integer> standings;

    private int                  timeout;

}
