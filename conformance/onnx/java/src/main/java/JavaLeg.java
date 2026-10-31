import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;
import java.io.FileInputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.DoubleBuffer;
import java.nio.LongBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Java leg of the export conformance check: loads the exported model and the golden batch (raw
 * little-endian files written by tma2.export.onnx_export), runs it, and prints the outputs as JSON
 * on stdout for the Python comparison. Usage: JavaLeg <export dir>.
 */
public final class JavaLeg {
  public static void main(String[] args) throws Exception {
    Path dir = Path.of(args.length > 0 ? args[0] : "export");
    String shapesJson = Files.readString(dir.resolve("shapes.json"));
    Map<String, long[]> shapes = parseShapes(shapesJson);
    OrtEnvironment env = OrtEnvironment.getEnvironment();
    try (OrtSession session = env.createSession(dir.resolve("toy.onnx").toString(), new OrtSession.SessionOptions())) {
      Map<String, OnnxTensor> feeds = new LinkedHashMap<>();
      for (Map.Entry<String, long[]> e : shapes.entrySet()) {
        String name = e.getKey();
        byte[] raw;
        try (FileInputStream in = new FileInputStream(dir.resolve("in_" + name + ".bin").toFile())) {
          raw = in.readAllBytes();
        }
        ByteBuffer bb = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        if (name.equals("k")) {
          LongBuffer lb = bb.asLongBuffer();
          long[] data = new long[lb.remaining()];
          lb.get(data);
          feeds.put(name, OnnxTensor.createTensor(env, LongBuffer.wrap(data), e.getValue()));
        } else {
          DoubleBuffer db = bb.asDoubleBuffer();
          double[] data = new double[db.remaining()];
          db.get(data);
          feeds.put(name, OnnxTensor.createTensor(env, DoubleBuffer.wrap(data), e.getValue()));
        }
      }
      try (OrtSession.Result result = session.run(feeds)) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, ai.onnxruntime.OnnxValue> e : result) {
          if (!first) sb.append(",");
          first = false;
          sb.append('"').append(e.getKey()).append("\":");
          Object v = e.getValue().getValue();
          sb.append(flatten(v));
        }
        sb.append("}");
        System.out.println(sb);
      }
    }
  }

  private static String flatten(Object v) {
    StringBuilder sb = new StringBuilder("[");
    appendFlat(v, sb);
    sb.append("]");
    return sb.toString();
  }

  private static void appendFlat(Object v, StringBuilder sb) {
    if (v instanceof double[] a) {
      for (double x : a) { if (sb.charAt(sb.length() - 1) != '[') sb.append(','); sb.append(x); }
    } else if (v instanceof float[] a) {
      for (float x : a) { if (sb.charAt(sb.length() - 1) != '[') sb.append(','); sb.append(x); }
    } else if (v instanceof Object[] a) {
      for (Object o : a) appendFlat(o, sb);
    }
  }

  private static Map<String, long[]> parseShapes(String json) {
    Map<String, long[]> out = new LinkedHashMap<>();
    String body = json.trim().replaceAll("^\\{|\\}$", "");
    for (String entry : body.split("\\],")) {
      String[] kv = entry.split(":", 2);
      String key = kv[0].replaceAll("[\"\\s]", "");
      String[] dims = kv[1].replaceAll("[\\[\\]\\s]", "").split(",");
      long[] shape = new long[dims.length];
      for (int i = 0; i < dims.length; i++) shape[i] = Long.parseLong(dims[i]);
      out.put(key, shape);
    }
    return out;
  }
}
