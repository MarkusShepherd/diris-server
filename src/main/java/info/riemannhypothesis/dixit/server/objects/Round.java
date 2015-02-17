package info.riemannhypothesis.dixit.server.objects;

import java.util.HashMap;
import java.util.Map;

import javax.jdo.annotations.IdGeneratorStrategy;
import javax.jdo.annotations.PersistenceCapable;
import javax.jdo.annotations.Persistent;
import javax.jdo.annotations.PrimaryKey;

import lombok.Getter;
import lombok.Setter;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.google.appengine.api.datastore.Key;

@PersistenceCapable
public class Round {

    public enum Status {
        WAITING, SUBMIT_STORY, SUBMIT_OTHERS, SUBMIT_VOTES, FINISHED
    }

    public static final int         MAX_DECEIVED_VOTE_SCORE                    = 3;
    public static final int         DECEIVED_VOTE_SCORE                        = 1;
    public static final int         ALL_CORRECT_SCORE                          = 2;
    public static final int         ALL_CORRECT_STORYTELLER_SCORE              = 0;
    public static final int         ALL_WRONG_SCORE                            = 2;
    public static final int         ALL_WRONG_STORYTELLER_SCORE                = 0;
    public static final int         NOT_ALL_CORRECT_OR_WRONG_SCORE             = 3;
    public static final int         NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE = 3;

    @Getter
    @PrimaryKey
    @Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
    private Key                     key;

    @Getter
    @JsonIgnore
    @Persistent
    private final Match             match;

    @Setter
    @Getter
    @Persistent
    private Key                     storyTellerKey;

    @Setter
    @Getter
    @Persistent
    private String                  story;

    @Getter
    @Persistent
    private final Map<Key, Key>     images;

    @Getter
    @Persistent
    private final Map<Key, Integer> scores;

    @Setter
    @Getter
    @Persistent
    private Status                  status;

    @Getter
    @Persistent
    private final Map<Key, Key>     votes;

    public Round(Match match) {
        this.match = match;
        images = new HashMap<Key, Key>();
        scores = new HashMap<Key, Integer>();
        votes = new HashMap<Key, Key>();
        status = Status.WAITING;
    }

    public boolean submissionComplete() {
        // TODO
        return false;
    }

    public boolean votesComplete() {
        // TODO
        return false;
    }

    public boolean calculateScores() {
        // TODO

        /* if (!(status == Status.SUBMIT_VOTES || status == Status.FINISHED) ||
         * !votesComplete()) { return false; }
         * 
         * boolean allCorrect = true; boolean allWrong = true;
         * 
         * int[] tempScores = new int[votes.length];
         * 
         * for (int i = 0; i < votes.length; i++) { if (i == storyTellerPos)
         * continue;
         * 
         * if (votes[i] == storyTellerPos) { allWrong = false; } else {
         * allCorrect = false; if (tempScores[votes[i]] <
         * MAX_DECEIVED_VOTE_SCORE) { tempScores[votes[i]] +=
         * DECEIVED_VOTE_SCORE; } } }
         * 
         * if (allCorrect || allWrong) { for (int i = 0; i < votes.length; i++)
         * { if (i != storyTellerPos) tempScores[i] += ALL_CORRECT_SCORE; } }
         * else { for (int i = 0; i < votes.length; i++) { if (i ==
         * storyTellerPos) tempScores[i] +=
         * NOT_ALL_CORRECT_OR_WRONG_STORYTELLER_SCORE; else if (votes[i] ==
         * storyTellerPos) tempScores[i] += NOT_ALL_CORRECT_OR_WRONG_SCORE; } }
         * 
         * scores = tempScores; status = Status.FINISHED; matchKey.update(); */

        return true;
    }
}
