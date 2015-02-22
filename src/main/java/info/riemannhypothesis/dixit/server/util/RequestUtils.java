package info.riemannhypothesis.dixit.server.util;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;

import javax.servlet.http.HttpServletRequest;

import org.apache.commons.fileupload.FileItemIterator;
import org.apache.commons.fileupload.FileItemStream;
import org.apache.commons.fileupload.FileUploadException;
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.apache.commons.io.IOUtils;

/**
 * @author Markus Schepke
 * @date 21 Feb 2015
 */
public class RequestUtils {

    public static final int DEFAULT_BUFFER_SIZE = 2 * 1024 * 1024;

    public static void copy(InputStream from, OutputStream to)
            throws IOException {
        copy(from, to, DEFAULT_BUFFER_SIZE);
    }

    /**
     * Transfer the data from the inputStream to the outputStream. Then close
     * both streams.
     * 
     * @throws IOException
     */
    public static void copy(InputStream from, OutputStream to, int bufferSize)
            throws IOException {
        try {
            byte[] buffer = new byte[bufferSize];
            int bytesRead = from.read(buffer);
            while (bytesRead != -1) {
                to.write(buffer, 0, bytesRead);
                bytesRead = from.read(buffer);
            }
        } finally {
            from.close();
            to.close();
        }
    }

    public static RequestFields getRequestFields(HttpServletRequest req)
            throws FileUploadException, IOException {
        RequestFields rf = new RequestFields();

        ServletFileUpload upload = new ServletFileUpload();
        FileItemIterator iterator = upload.getItemIterator(req);

        while (iterator.hasNext()) {
            FileItemStream item = iterator.next();
            InputStream stream = item.openStream();

            String name = item.getFieldName();

            if (item.isFormField()) {
                String content = IOUtils.toString(stream, "UTF-8");
                rf.formFields.put(name, content);
            } else {
                rf.fileFields.put(name, IOUtils.toByteArray(stream));
            }
        }

        return rf;
    }

    public static class RequestFields {
        public final Map<String, String> formFields = new HashMap<String, String>();
        public final Map<String, byte[]> fileFields = new HashMap<String, byte[]>();
    }
}
