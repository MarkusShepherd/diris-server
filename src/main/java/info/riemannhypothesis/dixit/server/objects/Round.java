package info.riemannhypothesis.dixit.server.objects;

import java.util.Map;

public class Round {

    private long                 id;

    private Match                match;

    private Player               storyTeller;
    private String               story;

    private Map<Player, Image>   images;

    private Map<Player, Integer> scores;

}
