/**
 * 
 */
package info.riemannhypothesis.dixit.server.util;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
public class ListUtils {

    public static <T> List<T> shuffledListFromSet(Set<T> set) {
        List<T> list = new ArrayList<T>(set);
        Collections.shuffle(list);
        return list;
    }

}