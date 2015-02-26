package info.riemannhypothesis.dixit.server.util;

import info.riemannhypothesis.dixit.server.Application;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Set;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
public class Utils {

    public static <T> List<T> shuffledListFromSet(Set<T> set) {
        List<T> list = new ArrayList<T>(set);
        Collections.shuffle(list);
        return list;
    }

    public static String now() {
        return Application.DATE_FORMATTER.format(new Date());
    }
}
